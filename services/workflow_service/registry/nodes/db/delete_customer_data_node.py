"""Workflow node to delete customer data documents discovered via system search.

This node mirrors the node patterns used in `customer_data.py` (load/store nodes):
- Uses a strongly typed Pydantic config schema with optional dynamic overrides from input
- Pulls execution context from `runtime_config` (application/external context)
- Interacts with `CustomerDataService` for search and per-document deletion

Behavioral requirements implemented:
- Parameters for search and delete come from node config; dynamic input can override them
- Uses `CustomerDataService.system_search_documents` to find documents
- Deletes versioned/unversioned documents using the appropriate service methods
- Fails the node by default if a delete fails for any found document (configurable)
- If no documents are found: logs a warning and returns successfully

Design notes and caveats:
- System search may return both versioning metadata and per-version entries for versioned docs.
  Deletion is deduplicated by the versionless path (namespace/docname) and executed once per doc.
- For system documents, the service path building ignores the concrete `org_id` value when
  `is_system_entity=True`; we pass the current job's `owner_org_id` for typing compatibility.
- `sort_by`/`sort_order` dynamic overrides accept enum instances or their string values and
  are converted to the corresponding enums when possible.
- Optional `continue_on_error` and `dry_run` are provided; by default, the node raises on first
  failure as requested. `max_deletes` can cap the number of deletes performed for safety.
"""

from __future__ import annotations

import uuid
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Type, Union

from pydantic import Field, ValidationError, model_validator

# Internal logging
from global_config.logger import get_prefect_or_regular_python_logger

# Workflow runtime and constants
from kiwi_app.workflow_app.constants import LaunchStatus
from kiwi_app.auth.models import User
from kiwi_app.workflow_app import schemas as wa_schemas
from kiwi_app.workflow_app.schemas import CustomerDocumentSearchResult
from kiwi_app.workflow_app.schemas import CustomerDocumentSearchResultMetadata
from kiwi_app.workflow_app.schemas import CustomerDataSortBy, SortOrder
from kiwi_app.workflow_app.schemas import CustomerDocumentMetadata  # typing reference
from kiwi_app.workflow_app.schemas import DocumentOperation  # unused, reference
from kiwi_app.workflow_app.schemas import DocumentOperationType  # unused, reference
from kiwi_app.workflow_app.schemas import DocumentOperationResult  # unused, reference

from kiwi_app.workflow_app.service_customer_data import CustomerDataService

from workflow_service.config.constants import (
    APPLICATION_CONTEXT_KEY,
    EXTERNAL_CONTEXT_MANAGER_KEY,
)

from workflow_service.registry.schemas.base import BaseNodeConfig, BaseSchema
from workflow_service.registry.nodes.core.dynamic_nodes import (
    BaseDynamicNode,
    DynamicSchema,
)


def _get_nested_obj(data: Any, field_path: str) -> Tuple[Any, bool]:
    """Retrieve a nested object/value by a dot-notation path from a dict/list structure.

    Matches the helper behavior used in other nodes so dynamic overrides work consistently.
    Returns (value, True) if found; (None, False) otherwise.
    """
    current = data
    if not field_path:
        return data, True
    for part in field_path.split("."):
        if isinstance(current, dict):
            if part in current:
                current = current[part]
            else:
                return None, False
        elif isinstance(current, list):
            try:
                idx = int(part)
            except (TypeError, ValueError):
                return None, False
            if 0 <= idx < len(current):
                current = current[idx]
            else:
                return None, False
        else:
            return None, False
    return current, True


def _resolve_search_patterns(
    search_params: DeleteSearchParams,
    full_input_data: Dict[str, Any],
) -> Optional[Tuple[str, str]]:
    """
    Resolves the namespace_pattern and docname_pattern for search operations.

    Handles static, dynamic (retrieved from input fields), and pattern-based resolution.

    Args:
        search_params: The DeleteSearchParams containing pattern resolution config.
        full_input_data: The complete input dict to resolve patterns from.

    Returns:
        A tuple (namespace_pattern, docname_pattern) or None if resolution fails.
    """
    logger = get_prefect_or_regular_python_logger(f"{__name__}._resolve_search_patterns")
    resolved_namespace_pattern: Optional[str] = None
    resolved_docname_pattern: Optional[str] = None

    # --- Resolve Namespace Pattern ---
    if search_params.namespace_pattern is not None:
        resolved_namespace_pattern = search_params.namespace_pattern
    elif search_params.input_namespace_field and not search_params.input_namespace_field_pattern:
        # Direct retrieval using input_namespace_field
        ns_val, found = _get_nested_obj(full_input_data, search_params.input_namespace_field)
        if found and isinstance(ns_val, str):
            resolved_namespace_pattern = ns_val
        else:
            logger.warning(f"Direct namespace field '{search_params.input_namespace_field}' not found in input or not a string.")
            return None
    elif search_params.input_namespace_field_pattern:
        # Pattern evaluation using data from input_namespace_field
        if not search_params.input_namespace_field:  # Should be caught by validator, but double-check
            logger.error("Config Error: input_namespace_field_pattern specified without input_namespace_field.")
            return None
        # Retrieve the object to use in the pattern context
        pattern_source_data, found = _get_nested_obj(full_input_data, search_params.input_namespace_field)
        if not found:
            logger.warning(f"Data for namespace pattern not found at '{search_params.input_namespace_field}' in input data.")
            return None
        try:
            # Use the retrieved object as 'item' in the pattern context
            resolved_namespace_pattern = search_params.input_namespace_field_pattern.format(item=pattern_source_data)
        except KeyError as e:
            logger.error(f"Error formatting input_namespace_field_pattern '{search_params.input_namespace_field_pattern}': Key {e} not found in data at '{search_params.input_namespace_field}'.")
            return None
        except Exception as e:
            logger.error(f"Error formatting input_namespace_field_pattern '{search_params.input_namespace_field_pattern}': {e}")
            return None
    else:
        # Should be caught by validator
        logger.error("Invalid DeleteSearchParams state for namespace_pattern.")
        return None

    # --- Resolve Docname Pattern ---
    if search_params.docname_pattern is not None:
        resolved_docname_pattern = search_params.docname_pattern
    elif search_params.input_docname_field and not search_params.input_docname_field_pattern:
        # Direct retrieval using input_docname_field
        dn_val, found = _get_nested_obj(full_input_data, search_params.input_docname_field)
        if found and isinstance(dn_val, str):
            resolved_docname_pattern = dn_val
        else:
            logger.warning(f"Direct docname field '{search_params.input_docname_field}' not found in input or not a string.")
            return None
    elif search_params.input_docname_field_pattern:
        # Pattern evaluation using data from input_docname_field
        if not search_params.input_docname_field:  # Should be caught by validator
            logger.error("Config Error: input_docname_field_pattern specified without input_docname_field.")
            return None
        # Retrieve the object to use in the pattern context
        pattern_source_data, found = _get_nested_obj(full_input_data, search_params.input_docname_field)
        if not found:
            logger.warning(f"Data for docname pattern not found at '{search_params.input_docname_field}' in input data.")
            return None
        try:
            # Use the retrieved object as 'item' in the pattern context
            resolved_docname_pattern = search_params.input_docname_field_pattern.format(item=pattern_source_data)
        except KeyError as e:
            logger.error(f"Error formatting input_docname_field_pattern '{search_params.input_docname_field_pattern}': Key {e} not found in data at '{search_params.input_docname_field}'.")
            return None
        except Exception as e:
            logger.error(f"Error formatting input_docname_field_pattern '{search_params.input_docname_field_pattern}': {e}")
            return None
    else:
        # Should be caught by validator
        logger.error("Invalid DeleteSearchParams state for docname_pattern.")
        return None

    # Final check
    if resolved_namespace_pattern is not None and resolved_docname_pattern is not None:
        return resolved_namespace_pattern, resolved_docname_pattern
    else:
        logger.error("Failed to resolve namespace_pattern or docname_pattern.")
        return None


class DeleteSearchParams(BaseNodeConfig):
    """Search parameters for locating documents to delete using system search.

    These map directly to `CustomerDataService.system_search_documents` parameters,
    except for `user` and `org_id`, which are sourced from runtime context.
    
    Supports static pattern values or dynamic generation from input data fields.
    """

    # Static Pattern Definition
    namespace_pattern: Optional[str] = Field(
        None, description="Static namespace pattern with wildcards, e.g., 'invoices*'"
    )
    docname_pattern: Optional[str] = Field(
        None, description="Static docname pattern with wildcards, e.g., '2025*'"
    )

    # Dynamic Retrieval from Input Data (direct value)
    input_namespace_field: Optional[str] = Field(
        None, description="Dot-notation path in the input data to retrieve the namespace_pattern value OR the object for pattern evaluation."
    )
    input_docname_field: Optional[str] = Field(
        None, description="Dot-notation path in the input data to retrieve the docname_pattern value OR the object for pattern evaluation."
    )

    # Pattern-Based Generation (using data from specific input field)
    input_namespace_field_pattern: Optional[str] = Field(
        None, description="f-string like template to generate the namespace_pattern using data found at 'input_namespace_field'. Uses {'item': retrieved_data} context."
    )
    input_docname_field_pattern: Optional[str] = Field(
        None, description="f-string like template to generate the docname_pattern using data found at 'input_docname_field'. Uses {'item': retrieved_data} context."
    )

    # Other search parameters
    text_search_query: Optional[str] = Field(
        None, description="Optional text search query for system search"
    )
    value_filter: Optional[Dict[str, Any]] = Field(
        None, description="Optional value-based filter applied during system search"
    )
    skip: int = Field(0, ge=0, description="Pagination: number of results to skip")
    limit: int = Field(1000, ge=1, description="Pagination: max number of results to return")
    sort_by: Optional[CustomerDataSortBy] = Field(
        None, description="Sort results by a supported field (e.g., created_at, updated_at)"
    )
    sort_order: Optional[SortOrder] = Field(
        SortOrder.DESC, description="Sort order for results (ASC or DESC)"
    )

    @model_validator(mode='after')
    def validate_pattern_sources(self) -> 'DeleteSearchParams':
        """Ensures a valid and unique combination of fields is provided for namespace_pattern and docname_pattern."""
        logger = get_prefect_or_regular_python_logger(f"{__name__}.DeleteSearchParams")
        
        # Namespace pattern validation
        ns_sources = [
            self.namespace_pattern,
            self.input_namespace_field and not self.input_namespace_field_pattern, # Field used directly
            self.input_namespace_field_pattern
        ]
        num_ns_sources = sum(1 for source in ns_sources if source) # Count how many are not None/False
        
        if num_ns_sources > 1:
            logger.error("Multiple namespace_pattern sources configured in DeleteSearchParams")
            raise ValueError("Provide only one source for namespace_pattern: namespace_pattern, input_namespace_field (direct), or input_namespace_field_pattern.")
        if num_ns_sources == 0:
            logger.error("No namespace_pattern source configured in DeleteSearchParams")
            raise ValueError("One source for namespace_pattern must be provided: namespace_pattern, input_namespace_field, or input_namespace_field_pattern.")
        
        # If using input_namespace_field_pattern, input_namespace_field must be set
        if self.input_namespace_field_pattern and not self.input_namespace_field:
            logger.error("input_namespace_field_pattern used without input_namespace_field")
            raise ValueError("'input_namespace_field' must be provided when using 'input_namespace_field_pattern'.")
        
        # Docname pattern validation
        dn_sources = [
            self.docname_pattern,
            self.input_docname_field and not self.input_docname_field_pattern, # Field used directly
            self.input_docname_field_pattern
        ]
        num_dn_sources = sum(1 for source in dn_sources if source) # Count how many are not None/False
        
        if num_dn_sources > 1:
            logger.error("Multiple docname_pattern sources configured in DeleteSearchParams")
            raise ValueError("Provide only one source for docname_pattern: docname_pattern, input_docname_field (direct), or input_docname_field_pattern.")
        if num_dn_sources == 0:
            logger.error("No docname_pattern source configured in DeleteSearchParams")
            raise ValueError("One source for docname_pattern must be provided: docname_pattern, input_docname_field, or input_docname_field_pattern.")
        
        # If using input_docname_field_pattern, input_docname_field must be set
        if self.input_docname_field_pattern and not self.input_docname_field:
            logger.error("input_docname_field_pattern used without input_docname_field")
            raise ValueError("'input_docname_field' must be provided when using 'input_docname_field_pattern'.")
        
        # Basic pattern validation (for f-string templates)
        if self.input_namespace_field_pattern and ('{' not in self.input_namespace_field_pattern or '}' not in self.input_namespace_field_pattern):
            logger.warning(f"input_namespace_field_pattern '{self.input_namespace_field_pattern}' doesn't look like a valid f-string pattern.")
        if self.input_docname_field_pattern and ('{' not in self.input_docname_field_pattern or '}' not in self.input_docname_field_pattern):
            logger.warning(f"input_docname_field_pattern '{self.input_docname_field_pattern}' doesn't look like a valid f-string pattern.")
        
        return self


class DeleteCustomerDataConfig(BaseNodeConfig):
    """Configuration schema for the DeleteCustomerDataNode.

    Supports static configuration and dynamic overrides from input data. When overrides
    are provided, they supersede the static config values.
    """

    # Static search parameters (required unless dynamic overrides provided and complete)
    search_params: Optional[DeleteSearchParams] = Field(
        None,
        description="Static search parameters. Can be overridden via `search_params_input_path`."
    )

    # Dynamic config overrides from input
    search_params_input_path: Optional[str] = Field(
        None,
        description="Path in input data to an object with search parameters; overrides static values if present.",
    )
    delete_options_input_path: Optional[str] = Field(
        None,
        description="Path in input data to an object with delete options (dry_run, max_deletes, continue_on_error, on_behalf_of_user_id).",
    )

    # Delete options
    dry_run: bool = Field(
        False, description="If True, do not delete; only return which documents would be deleted."
    )
    continue_on_error: bool = Field(
        False,
        description="If True, continue deleting remaining documents even if one delete fails. By default, the node fails on first delete error.",
    )
    max_deletes: Optional[int] = Field(
        None, ge=1, description="Optional cap on the number of documents to delete."
    )
    on_behalf_of_user_id: Optional[str] = Field(
        None,
        description="Optional user ID (UUID string) to act on behalf of when deleting (superuser only).",
    )

    @model_validator(mode="after")
    def _validate_search_source(self) -> "DeleteCustomerDataConfig":
        """Ensure we have a way to obtain search parameters (static or dynamic)."""
        if self.search_params is None and not self.search_params_input_path:
            raise ValueError(
                "Either 'search_params' or 'search_params_input_path' must be provided."
            )
        return self


class DeleteCustomerDataOutput(BaseSchema):
    """Output for DeleteCustomerDataNode.

    Includes counts and the list of documents deleted (or that would be deleted in dry run).
    """

    found_count: int = Field(0, description="Number of documents found by the search")
    deleted_count: int = Field(0, description="Number of documents successfully deleted")
    dry_run: bool = Field(False, description="Indicates whether this was a dry run")
    deleted_documents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of deleted documents with identifying metadata",
    )
    failures: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of failures with document identifiers and error messages (only populated if continue_on_error=True)",
    )


class DeleteCustomerDataNode(BaseDynamicNode):
    """Node to delete customer data documents discovered via a system-level search.

    The node uses `CustomerDataService.system_search_documents` to identify documents
    and then deletes each document using either versioned or unversioned delete APIs.
    """

    node_name: ClassVar[str] = "delete_customer_data"
    node_version: ClassVar[str] = "0.1.0"
    env_flag: ClassVar[LaunchStatus] = LaunchStatus.PRODUCTION

    output_schema_cls: ClassVar[Type[DeleteCustomerDataOutput]] = DeleteCustomerDataOutput
    config_schema_cls: ClassVar[Type[DeleteCustomerDataConfig]] = DeleteCustomerDataConfig
    config: DeleteCustomerDataConfig

    async def _resolve_effective_search_params(
        self, input_dict: Dict[str, Any]
    ) -> Tuple[DeleteSearchParams, str, str]:
        """Resolve effective search params by overlaying dynamic overrides over static config.
        
        Also resolves the final namespace_pattern and docname_pattern values using the
        pattern resolution logic.

        Priority: values from `search_params_input_path` override static `search_params`.
        
        Returns:
            Tuple containing:
                - DeleteSearchParams: The resolved search parameters
                - str: Resolved namespace_pattern
                - str: Resolved docname_pattern
        """
        static_params_dict: Dict[str, Any] = (
            self.config.search_params.model_dump(exclude_none=True)
            if self.config.search_params is not None
            else {}
        )

        # Apply dynamic overrides if present
        if self.config.search_params_input_path:
            dyn_obj, found = _get_nested_obj(input_dict, self.config.search_params_input_path)
            if found and isinstance(dyn_obj, dict):
                overrides = {k: v for k, v in dyn_obj.items() if v is not None}

                # Convert enum strings if necessary
                if "sort_by" in overrides and isinstance(overrides["sort_by"], str):
                    try:
                        overrides["sort_by"] = CustomerDataSortBy(overrides["sort_by"])  # type: ignore[arg-type]
                    except Exception:
                        self.warning(
                            f"Unknown sort_by value '{overrides['sort_by']}', ignoring override."
                        )
                        overrides.pop("sort_by", None)
                if "sort_order" in overrides and isinstance(overrides["sort_order"], str):
                    try:
                        overrides["sort_order"] = SortOrder(overrides["sort_order"])  # type: ignore[arg-type]
                    except Exception:
                        self.warning(
                            f"Unknown sort_order value '{overrides['sort_order']}', ignoring override."
                        )
                        overrides.pop("sort_order", None)

                static_params_dict.update(overrides)
            elif self.config.search_params is None:
                # No static params and dynamic path missing/invalid
                raise ValueError(
                    f"Data at '{self.config.search_params_input_path}' is missing or not a dict; cannot derive search params."
                )

        # Validate into DeleteSearchParams (this will trigger our new validation logic)
        try:
            effective_search_params = DeleteSearchParams.model_validate(static_params_dict)
        except ValidationError as ve:
            self.error(
                f"Validation error constructing DeleteSearchParams from merged input/config: {ve}"
            )
            raise

        # Resolve the final namespace_pattern and docname_pattern values
        resolved_patterns = _resolve_search_patterns(effective_search_params, input_dict)
        if not resolved_patterns:
            raise ValueError("Failed to resolve namespace_pattern and docname_pattern from the configuration and input data.")
        
        resolved_namespace_pattern, resolved_docname_pattern = resolved_patterns
        
        return effective_search_params, resolved_namespace_pattern, resolved_docname_pattern

    def _apply_delete_option_overrides(self, input_dict: Dict[str, Any]) -> None:
        """Apply delete option overrides from input if configured.

        Mutates `self.config` fields for: dry_run, max_deletes, continue_on_error, on_behalf_of_user_id.
        """
        if not self.config.delete_options_input_path:
            return
        dyn_obj, found = _get_nested_obj(input_dict, self.config.delete_options_input_path)
        if not (found and isinstance(dyn_obj, dict)):
            return

        # Only update known option keys if provided
        for key in [
            "dry_run",
            "max_deletes",
            "continue_on_error",
            "on_behalf_of_user_id",
        ]:
            if key in dyn_obj and dyn_obj[key] is not None:
                try:
                    setattr(self.config, key, dyn_obj[key])
                except Exception:
                    self.warning(f"Failed to apply delete option override for '{key}'.")

    async def process(
        self,
        input_data: Union[DynamicSchema, Dict[str, Any]],
        runtime_config: Optional[Dict[str, Any]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> DeleteCustomerDataOutput:
        """Locate and delete customer data documents using a system search.

        Steps:
        1. Resolve effective search params (static config overlaid by input overrides)
        2. Execute system search via `CustomerDataService.system_search_documents`
        3. Deduplicate versioned results by versionless path
        4. Delete each located document (respecting dry_run / max_deletes)
        5. Fail by default on first error; can be relaxed via `continue_on_error`
        """

        input_dict: Dict[str, Any] = (
            input_data if isinstance(input_data, dict) else input_data.model_dump(mode="json")
        )

        if not runtime_config:
            self.error("Missing runtime_config.")
            return self.__class__.output_schema_cls(
                found_count=0, deleted_count=0, dry_run=self.config.dry_run
            )

        rc = runtime_config.get("configurable") if isinstance(runtime_config, dict) else None
        app_context: Optional[Dict[str, Any]] = (rc or {}).get(APPLICATION_CONTEXT_KEY)
        ext_context = (rc or {}).get(EXTERNAL_CONTEXT_MANAGER_KEY)
        if not app_context or not ext_context:
            self.error(
                f"Missing required keys in runtime_config: {APPLICATION_CONTEXT_KEY} or {EXTERNAL_CONTEXT_MANAGER_KEY}"
            )
            return self.__class__.output_schema_cls(
                found_count=0, deleted_count=0, dry_run=self.config.dry_run
            )

        user: Optional[User] = app_context.get("user")
        run_job = app_context.get("workflow_run_job")
        if not user or not run_job:
            self.error("Missing 'user' or 'workflow_run_job' in application_context.")
            return self.__class__.output_schema_cls(
                found_count=0, deleted_count=0, dry_run=self.config.dry_run
            )

        # Resolve search params and delete option overrides
        try:
            effective_search, resolved_namespace_pattern, resolved_docname_pattern = await self._resolve_effective_search_params(
                input_dict
            )
        except Exception as e:
            # Already logged
            raise

        self._apply_delete_option_overrides(input_dict)

        # Extract on_behalf_of_user_id if provided
        on_behalf_uuid: Optional[uuid.UUID] = None
        if self.config.on_behalf_of_user_id:
            try:
                on_behalf_uuid = uuid.UUID(self.config.on_behalf_of_user_id)
            except ValueError:
                self.error(
                    f"Invalid UUID format for on_behalf_of_user_id: '{self.config.on_behalf_of_user_id}'."
                )
                raise

        customer_data_service: CustomerDataService = ext_context.customer_data_service

        # Execute system search
        try:
            search_results: List[CustomerDocumentSearchResult] = (
                await customer_data_service.system_search_documents(
                    namespace_pattern=resolved_namespace_pattern,
                    docname_pattern=resolved_docname_pattern,
                    text_search_query=effective_search.text_search_query,
                    value_filter=effective_search.value_filter,
                    skip=effective_search.skip,
                    limit=effective_search.limit,
                    sort_by=effective_search.sort_by,
                    sort_order=effective_search.sort_order,
                    is_called_from_workflow=True,
                    user=user,
                    org_id=run_job.owner_org_id,
                    search_used_for_mutation=True,
                )
            )
        except Exception as e:
            self.error(f"System search failed: {e}", exc_info=True)
            raise

        if not search_results:
            self.warning(
                f"DeleteCustomerDataNode: No documents found for namespace='{resolved_namespace_pattern}', docname='{resolved_docname_pattern}'."
            )
            return self.__class__.output_schema_cls(
                found_count=0, deleted_count=0, dry_run=self.config.dry_run
            )

        # Deduplicate by versionless path (namespace/docname), since versioned docs may produce many rows
        unique_by_versionless: Dict[str, CustomerDocumentSearchResultMetadata] = {}
        for item in search_results:
            meta: CustomerDocumentSearchResultMetadata = item.metadata
            if not isinstance(meta, CustomerDocumentSearchResultMetadata):
                # Defensive: accommodate raw dicts if any
                try:
                    meta = CustomerDocumentSearchResultMetadata(**item.get("metadata", {}))  # type: ignore[assignment]
                except Exception:
                    self.warning("Encountered search result with invalid metadata; skipping.")
                    continue

            # Skip metadata rows only if they carry no identifying path; otherwise dedupe them away
            versionless_path: Optional[str] = getattr(meta, "versionless_path", None)
            if not versionless_path:
                # Fallback path key using components
                org_id_segment = (
                    str(meta.org_id) if getattr(meta, "org_id", None) else "SYSTEM"
                )
                versionless_path = f"{org_id_segment}/{meta.user_id_or_shared_placeholder}/{meta.namespace}/{meta.docname}"

            # Keep the first encountered metadata per versionless path
            if versionless_path not in unique_by_versionless:
                unique_by_versionless[versionless_path] = meta

        # Apply max_deletes cap if any
        targets: List[CustomerDocumentSearchResultMetadata] = list(
            unique_by_versionless.values()
        )
        if self.config.max_deletes is not None:
            targets = targets[: self.config.max_deletes]

        self.info(
            f"DeleteCustomerDataNode: Found {len(unique_by_versionless)} unique documents;"
            f" proceeding with {len(targets)} delete(s){' (dry run)' if self.config.dry_run else ''}. For namespace='{resolved_namespace_pattern}', docname='{resolved_docname_pattern}'."
        )

        # Perform deletions
        deleted_docs: List[Dict[str, Any]] = []
        failures: List[Dict[str, Any]] = []

        if self.config.dry_run:
            # Only report targets
            for meta in targets:
                deleted_docs.append(
                    {
                        "org_id": str(meta.org_id) if getattr(meta, "org_id", None) else None,
                        "namespace": meta.namespace,
                        "docname": meta.docname,
                        "is_shared": bool(meta.is_shared),
                        "is_versioned": bool(meta.is_versioned),
                        "is_system_entity": bool(meta.is_system_entity),
                    }
                )
            return self.__class__.output_schema_cls(
                found_count=len(unique_by_versionless),
                deleted_count=0,
                dry_run=True,
                deleted_documents=deleted_docs,
                failures=[],
            )

        # Execute actual deletes
        for meta in targets:
            target_org_id = meta.org_id or run_job.owner_org_id
            try:
                if meta.is_versioned:
                    success = await customer_data_service.delete_versioned_document(
                        org_id=target_org_id,
                        namespace=meta.namespace,
                        docname=meta.docname,
                        is_shared=bool(meta.is_shared),
                        user=user,  # type: ignore[arg-type]
                        on_behalf_of_user_id=on_behalf_uuid,
                        is_system_entity=bool(meta.is_system_entity),
                        is_called_from_workflow=True,
                        lock=True,
                    )
                else:
                    success = await customer_data_service.delete_unversioned_document(
                        org_id=target_org_id,
                        namespace=meta.namespace,
                        docname=meta.docname,
                        is_shared=bool(meta.is_shared),
                        user=user,  # type: ignore[arg-type]
                        on_behalf_of_user_id=on_behalf_uuid,
                        is_system_entity=bool(meta.is_system_entity),
                        is_called_from_workflow=True,
                    )

                if not success:
                    raise RuntimeError(
                        f"Delete returned False for '{meta.namespace}/{meta.docname}'."
                    )

                deleted_docs.append(
                    {
                        "org_id": str(meta.org_id) if getattr(meta, "org_id", None) else None,
                        "namespace": meta.namespace,
                        "docname": meta.docname,
                        "is_shared": bool(meta.is_shared),
                        "is_versioned": bool(meta.is_versioned),
                        "is_system_entity": bool(meta.is_system_entity),
                    }
                )

            except Exception as e:
                self.error(
                    f"Failed to delete document '{meta.namespace}/{meta.docname}': {e}",
                    exc_info=True,
                )
                if self.config.continue_on_error:
                    failures.append(
                        {
                            "org_id": str(meta.org_id)
                            if getattr(meta, "org_id", None)
                            else None,
                            "namespace": meta.namespace,
                            "docname": meta.docname,
                            "is_shared": bool(meta.is_shared),
                            "is_versioned": bool(meta.is_versioned),
                            "is_system_entity": bool(meta.is_system_entity),
                            "error": str(e),
                        }
                    )
                    continue
                # Default: fail fast as requested
                raise

        return self.__class__.output_schema_cls(
            found_count=len(unique_by_versionless),
            deleted_count=len(deleted_docs),
            dry_run=False,
            deleted_documents=deleted_docs,
            failures=failures,
        )


if __name__ == "__main__":
    # Basic schema validation self-check - static patterns
    _ = DeleteCustomerDataConfig(
        search_params=DeleteSearchParams(
            namespace_pattern="test*", docname_pattern="doc*"
        )
    )
    
    # Test with dynamic field patterns
    _ = DeleteCustomerDataConfig(
        search_params=DeleteSearchParams(
            input_namespace_field="search_criteria.namespace",
            input_docname_field="search_criteria.docname",
        )
    )
    
    # Test with pattern-based generation
    _ = DeleteCustomerDataConfig(
        search_params=DeleteSearchParams(
            input_namespace_field="search_criteria",
            input_namespace_field_pattern="{item[prefix]}*",
            input_docname_field="search_criteria",
            input_docname_field_pattern="{item[suffix]}*",
        )
    )
    
    logger = get_prefect_or_regular_python_logger(__name__)
    logger.info("DeleteCustomerDataNode config schema validated with all pattern types.")


