"""
Document setup and cleanup configuration for B2B Blog SEO/AEO Scoring workflow testing.
"""

from typing import List
from kiwi_client.test_run_workflow_client import SetupDocInfo, CleanupDocInfo

# Test parameters for B2B Blog SEO/AEO Scoring workflow
test_namespace = "test_blog_posts_b2b_scoring"
test_docname = "sample_ai_healthcare_blog_post"
test_is_shared = False


def get_setup_docs() -> List[SetupDocInfo]:
    """
    Get the list of documents to set up for testing.
    
    Returns:
        List of SetupDocInfo configurations for test documents.
    """
    return [
        {
            'namespace': test_namespace,
            'docname': test_docname,
            'initial_data': {
                "title": "The Future of AI in Healthcare: Transforming Patient Care in 2024",
                "content": """
# The Future of AI in Healthcare: Transforming Patient Care in 2024

Artificial intelligence (AI) is revolutionizing healthcare at an unprecedented pace. As we progress through 2024, the integration of AI technologies in medical practice has moved from experimental to essential, fundamentally changing how we diagnose, treat, and care for patients.

## What is AI in Healthcare?

AI in healthcare refers to the use of machine learning algorithms and software to emulate human cognition in analyzing, interpreting, and understanding complex medical data. This technology encompasses everything from diagnostic imaging to drug discovery and personalized treatment plans.

## Key Applications of AI in Modern Healthcare

### 1. Diagnostic Imaging and Radiology

AI-powered imaging systems have achieved remarkable accuracy rates, often surpassing human radiologists in detecting certain conditions:

- **Medical Imaging Analysis**: AI can identify cancerous tumors, fractures, and other abnormalities with 95%+ accuracy
- **Early Disease Detection**: Machine learning algorithms can spot early signs of diseases like Alzheimer's and Parkinson's
- **Workflow Optimization**: Automated image analysis reduces diagnostic time by up to 50%

### 2. Personalized Treatment Plans

Modern AI systems analyze patient data to create customized treatment protocols:

- **Genetic Analysis**: AI processes genomic data to predict treatment responses
- **Drug Interaction Monitoring**: Algorithms identify potential medication conflicts
- **Treatment Outcome Prediction**: Machine learning models forecast patient recovery timelines

### 3. Clinical Decision Support Systems

AI assists healthcare professionals in making informed decisions:

- **Real-time Risk Assessment**: Continuous monitoring of patient vital signs
- **Evidence-based Recommendations**: AI reviews latest medical literature for treatment options
- **Preventive Care Alerts**: Early warning systems for potential health complications

## Benefits of AI in Healthcare

The integration of AI technologies brings numerous advantages to healthcare delivery:

**Improved Accuracy**: AI systems can process vast amounts of data without fatigue, leading to more accurate diagnoses and treatment recommendations.

**Enhanced Efficiency**: Automated processes reduce administrative burden and allow healthcare professionals to focus on patient care.

**Cost Reduction**: AI optimization can reduce healthcare costs by up to 30% through improved resource allocation and reduced errors.

**Accessibility**: AI-powered telemedicine and diagnostic tools make healthcare more accessible to underserved populations.

## Challenges and Considerations

Despite its promise, AI in healthcare faces several challenges:

### Data Privacy and Security
- Patient data protection remains paramount
- HIPAA compliance requirements for AI systems
- Cybersecurity concerns with connected medical devices

### Regulatory Compliance
- FDA approval processes for AI medical devices
- International regulatory harmonization efforts
- Liability and malpractice considerations

### Integration Complexity
- Legacy system compatibility issues
- Staff training and adaptation requirements
- Change management in healthcare organizations

## The Road Ahead: AI Healthcare Trends for 2024 and Beyond

Looking forward, several trends will shape the future of AI in healthcare:

1. **Predictive Analytics**: Advanced algorithms will predict health outcomes before symptoms appear
2. **Voice-Activated AI**: Natural language processing will enable hands-free medical documentation
3. **Robotic Surgery**: AI-assisted surgical procedures will become more precise and minimally invasive
4. **Mental Health AI**: Therapeutic chatbots and mood analysis tools will support mental health care
5. **Drug Discovery Acceleration**: AI will reduce pharmaceutical development timelines from decades to years

## Conclusion

The future of AI in healthcare is not just promising – it's already here. As we continue through 2024, healthcare organizations that embrace AI technologies will be better positioned to deliver superior patient outcomes, reduce costs, and advance medical science.

For healthcare professionals, patients, and policymakers, understanding and adapting to these AI-driven changes is crucial for participating in the healthcare transformation that's reshaping our world.

---

*This article was written to provide insights into the current state and future potential of AI in healthcare. For specific medical advice, always consult with qualified healthcare professionals.*
                """,
                "meta_description": "Discover how AI is transforming healthcare in 2024. Learn about diagnostic imaging, personalized treatment, and the future of patient care with artificial intelligence.",
                "author": "Dr. Sarah Johnson",
                "publication_date": "2024-03-15",
                "tags": ["AI", "Healthcare", "Medical Technology", "Digital Health", "Innovation"],
                "word_count": 750
            },
            'is_shared': test_is_shared,
            'is_versioned': False,
            'initial_version': "None",
            'is_system_entity': False
        }
    ]


def get_cleanup_docs() -> List[CleanupDocInfo]:
    """
    Get the list of documents to clean up after testing.
    
    Returns:
        List of CleanupDocInfo configurations for test document cleanup.
    """
    return [
        {
            'namespace': test_namespace,
            'docname': test_docname,
            'is_shared': test_is_shared,
            'is_versioned': False,
            'is_system_entity': False
        }
    ]


# Export for convenience
setup_docs = get_setup_docs()
cleanup_docs = get_cleanup_docs()
