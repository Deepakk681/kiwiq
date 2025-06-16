# KiwiQ Email Template System

A comprehensive Jinja2-based email template rendering system with email-specific Pydantic data models and component-based architecture for maximum type safety and maintainability.

## 🚀 Features

- **Email-Specific Data Models**: Dedicated Pydantic models for each email type ensuring type safety
- **Dual Format Support**: Generate both HTML and plain text versions of all emails
- **Component-Based Templates**: Reusable components for footers, buttons, lists, and text elements
- **Template Inheritance**: Base template system with consistent styling and responsive design
- **HTML to Text Conversion**: Intelligent conversion preserving links and formatting
- **Default Configurations**: Pre-configured KiwiQ branding and footer information
- **Email Client Compatibility**: Inline CSS styling for maximum email client compatibility

## 📁 Directory Structure

```
email_templates/
├── base.html                           # Base template with responsive layout and CSS
├── welcome.html                        # Welcome email for new users
├── account_confirmation.html           # Email verification template
├── first_steps_guide.html             # Onboarding guide template
├── draft_progress_reminder.html       # Draft completion reminder
├── achievement_milestone.html         # User milestone celebration
├── gentle_reminder.html               # Re-engagement for inactive users
├── notification.html                  # General notification template
├── components/
│   ├── footer.html                    # Footer with company info and unsubscribe
│   ├── button.html                    # CTA button component
│   ├── lists.html                     # List rendering macros
│   ├── text.html                      # Text and link formatting
│   ├── signature.html                 # Email signature component
│   └── support.html                   # Support contact component
├── samples/
│   ├── base_sample_inline.html        # Original inline CSS sample
│   └── base_sample.html               # Original external CSS sample
├── rendered_samples/                  # Generated email samples (HTML & TXT)
├── renderer.py                        # Main rendering engine and data models
└── README.md                          # This documentation
```

## 🛠 Quick Start

### Basic Welcome Email

```python
from renderer import EmailRenderer, WelcomeEmailData

# Create an email renderer
renderer = EmailRenderer()

# Create welcome email data
welcome_data = WelcomeEmailData(
    user_name="John Doe",
    congratulations_message="🎉 Welcome to KiwiQ! Your journey starts here.",
    action_button_url="https://app.kiwiq.com/dashboard"
)

# Render HTML and text versions
welcome_html = renderer.render_welcome_email(welcome_data)
welcome_text = renderer.render_welcome_email_as_text(welcome_data)

# Save or send the email
with open("welcome_email.html", "w") as f:
    f.write(welcome_html)
with open("welcome_email.txt", "w") as f:
    f.write(welcome_text)
```

### Account Confirmation Email

```python
from renderer import AccountConfirmationEmailData, FooterData

# Custom footer with unsubscribe link
custom_footer = FooterData(
    unsubscribe_link="https://app.kiwiq.com/unsubscribe?token=abc123"
)

confirmation_data = AccountConfirmationEmailData(
    user_name="Alice Johnson",
    confirmation_url="https://app.kiwiq.com/confirm?token=abc123xyz",
    expiry_hours=24,
    footer=custom_footer
)

# Render both formats
html = renderer.render_account_confirmation_email(confirmation_data)
text = renderer.render_account_confirmation_email_as_text(confirmation_data)
```

## 📊 Email-Specific Data Models

### Base Model

#### `BaseEmailData`
All email models inherit from this base class.

```python
class BaseEmailData(BaseModel):
    user_name: str                         # Recipient's name (required)
    footer: FooterData                     # Footer configuration with defaults
```

#### `FooterData`
Footer configuration with KiwiQ defaults.

```python
class FooterData(BaseModel):
    company_name: str = "KiwiQ AI"         # Company name
    company_address: str = "San Francisco, CA"  # Company address
    unsubscribe_link: Optional[str] = None # Unsubscribe URL
    support_email: str = "support@kiwiq.ai"  # Support contact
    powered_by_name: str = "KiwiQ Platform"  # Powered by text
    powered_by_url: str = "https://kiwiq.ai"  # Powered by URL
    help_center_url: str = "https://help.kiwiq.ai"  # Help center
```

### Email-Specific Models

#### `WelcomeEmailData`
New user welcome email with feature highlights.

```python
class WelcomeEmailData(BaseEmailData):
    congratulations_message: str           # Welcome message with emoji
    action_button_url: str                 # Main CTA button URL
    features_page_url: str                 # Features page link
```

#### `AccountConfirmationEmailData`
Email verification with confirmation link.

```python
class AccountConfirmationEmailData(BaseEmailData):
    confirmation_url: str                  # Account confirmation link (required)
    expiry_hours: int = 24                 # Link expiry time in hours
```

#### `FirstStepsGuideEmailData`
Onboarding guide with action steps.

```python
class FirstStepsGuideEmailData(BaseEmailData):
    start_writing_url: str                 # Link to create first post
    explore_ideas_url: str                 # Link to content ideas
    calendar_url: str                      # Link to content calendar
```

#### `DraftProgressReminderEmailData`
Urgent reminder for draft completion.

```python
class DraftProgressReminderEmailData(BaseEmailData):
    brief_title: str                       # Draft post title/topic
    publication_time: str                  # Scheduled publication time
    complete_post_url: str                 # Link to complete draft
    calendar_url: str                      # Link to reschedule
```

#### `AchievementMilestoneEmailData`
Celebration of user milestones.

```python
class AchievementMilestoneEmailData(BaseEmailData):
    posts_published: int                   # Number of posts published
    consistency_streak_weeks: int          # Consistency streak in weeks
    next_milestone_target: str             # Next achievement description
    content_journey_url: str               # Link to stats/analytics
```

#### `GentleReminderEmailData`
Re-engagement for inactive users.

```python
class GentleReminderEmailData(BaseEmailData):
    draft_posts_count: int                 # Number of draft posts waiting
    new_ideas_count: int                   # Number of new content ideas
    scheduled_posts_count: int             # Number of scheduled posts
    calendar_url: str                      # Link to review calendar
```

#### `NotificationEmailData`
General purpose notification email.

```python
class NotificationEmailData(BaseEmailData):
    message: str                           # Main notification message
    action_button_text: Optional[str] = None  # CTA button text
    action_button_url: Optional[str] = None   # CTA button URL
```

## 🎨 Available Email Templates

### User Onboarding
- **Welcome Email** (`welcome.html`) - New user welcome with congratulations
- **Account Confirmation** (`account_confirmation.html`) - Email verification
- **First Steps Guide** (`first_steps_guide.html`) - Onboarding with action steps

### User Engagement
- **Draft Progress Reminder** (`draft_progress_reminder.html`) - Urgent draft completion
- **Achievement Milestone** (`achievement_milestone.html`) - Celebration of milestones
- **Gentle Reminder** (`gentle_reminder.html`) - Re-engagement for inactive users

### General Communication
- **Notification** (`notification.html`) - General purpose notifications

## 🔧 Rendering Methods

### HTML Rendering
Each email type has a dedicated rendering method:

```python
renderer = EmailRenderer()

# Welcome email
html = renderer.render_welcome_email(welcome_data)

# Account confirmation
html = renderer.render_account_confirmation_email(confirmation_data)

# First steps guide
html = renderer.render_first_steps_guide_email(first_steps_data)

# Draft reminder
html = renderer.render_draft_progress_reminder_email(reminder_data)

# Achievement milestone
html = renderer.render_achievement_milestone_email(milestone_data)

# Gentle reminder
html = renderer.render_gentle_reminder_email(gentle_reminder_data)

# General notification
html = renderer.render_notification_email(notification_data)
```

### Plain Text Rendering
Each email type also supports text-only rendering:

```python
# All email types have corresponding text rendering methods
text = renderer.render_welcome_email_as_text(welcome_data)
text = renderer.render_account_confirmation_email_as_text(confirmation_data)
text = renderer.render_first_steps_guide_email_as_text(first_steps_data)
text = renderer.render_draft_progress_reminder_email_as_text(reminder_data)
text = renderer.render_achievement_milestone_email_as_text(milestone_data)
text = renderer.render_gentle_reminder_email_as_text(gentle_reminder_data)
text = renderer.render_notification_email_as_text(notification_data)
```

## 🏗 Template Architecture

### Template Inheritance
- **`base.html`**: Core responsive layout with CSS and email structure
- **Email templates**: Extend base template with specific content blocks
- **Components**: Reusable Jinja2 macros for consistent rendering

### Component System
Located in `components/` directory:
- **`footer.html`**: Company information and unsubscribe links
- **`button.html`**: CTA buttons with primary/secondary styling
- **`lists.html`**: Bullet points and nested list rendering
- **`text.html`**: Text formatting and inline links
- **`signature.html`**: Email signature component
- **`support.html`**: Support contact information

### HTML to Text Conversion
The `html_to_text()` method provides intelligent conversion:
- Converts `<a href="url">text</a>` to `text (url)` format
- Preserves list structure with bullet points
- Maintains proper spacing and line breaks
- Removes CSS and styling while preserving content structure
- Handles email-specific formatting requirements

## 🧪 Testing and Examples

### Run Example Generation

```bash
cd services/kiwi_app/email/email_templates
python renderer.py
```

This generates sample emails in `rendered_samples/`:
- `welcome_email.html` & `.txt`
- `account_confirmation_email.html` & `.txt`
- `first_steps_guide_email.html` & `.txt`
- `draft_progress_reminder_email.html` & `.txt`
- `achievement_milestone_email.html` & `.txt`
- `gentle_reminder_email.html` & `.txt`
- `general_notification_email.html` & `.txt`
- `index.html` - Browse all samples in your browser

### View Generated Samples

Open `rendered_samples/index.html` in your browser to see all email templates with both HTML and text formats.

## 📝 Best Practices

### 1. Use Email-Specific Models
Each email type has its own data model for better type safety:

```python
# Good - Type-safe with validation
welcome_data = WelcomeEmailData(
    user_name="John Doe",
    congratulations_message="Welcome!",
    action_button_url="https://app.kiwiq.com"
)

# Avoid - Generic dictionaries without validation
data = {"user_name": "John", "message": "Welcome"}
```

### 2. Leverage Default Values
Models come with sensible defaults - only override what you need:

```python
# Minimal configuration uses all defaults
data = WelcomeEmailData(user_name="John Doe")

# Custom configuration overrides specific values
data = WelcomeEmailData(
    user_name="John Doe",
    congratulations_message="🎉 Custom welcome message!"
)
```

### 3. Always Generate Both Formats
Provide both HTML and text versions for maximum compatibility:

```python
html_content = renderer.render_welcome_email(data)
text_content = renderer.render_welcome_email_as_text(data)

# Send both versions in your email client
```

### 4. Test Email Client Compatibility
- Gmail (web, mobile)
- Outlook (desktop, web, mobile)
- Apple Mail
- Yahoo Mail
- Thunderbird

## 🔍 Troubleshooting

### Common Issues

1. **Template Not Found**
   - Ensure you're using the correct template name
   - Check that template files exist in the templates directory
   - Verify file permissions and paths

2. **Pydantic Validation Errors**
   - Check required fields are provided
   - Verify data types match model definitions
   - Review field validation rules

3. **Rendering Errors**
   - Validate Jinja2 template syntax
   - Check component imports are correct
   - Ensure template inheritance is properly configured

### Debug Information

```python
renderer = EmailRenderer()
print(f"Template directory: {renderer.template_dir}")
print(f"Available templates: {list(renderer.template_dir.glob('*.html'))}")

# Test data model validation
try:
    data = WelcomeEmailData(user_name="Test User")
    print(f"Model validation successful: {data}")
except Exception as e:
    print(f"Validation error: {e}")
```

## 🚧 Development Notes

### Design Decisions
- **Email-specific models**: Each email type has its own data model for better maintainability and type safety
- **Jinja2 template engine**: Powerful inheritance and macro system
- **Pydantic validation**: Ensures data integrity and provides clear error messages
- **Dual format rendering**: HTML for rich clients, text for compatibility
- **Component architecture**: Reusable components for consistent styling

### Caveats
- Email client CSS support varies significantly - test thoroughly
- Some HTML features may not work in all email clients
- Text conversion is best-effort - review generated text for quality
- Template loading assumes consistent directory structure

### Future Enhancements
- Email template preview functionality in web interface
- A/B testing support for different email variants
- Internationalization (i18n) support for multiple languages
- Visual email template editor
- Email delivery analytics and tracking
- Dynamic content personalization system

## 📄 License

Part of the KiwiQ platform. All rights reserved. 