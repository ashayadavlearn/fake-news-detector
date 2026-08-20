"""
forms.py
Flask-WTF forms. Every form gets CSRF protection automatically because
the app registers CSRFProtect() globally in app.py.
"""

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    remember = BooleanField("Remember me")


class DetectForm(FlaskForm):
    news_text = TextAreaField(
        "News headline or article",
        validators=[DataRequired(message="Please paste a headline or article to analyze."),
                    Length(min=10, max=20000, message="Please enter at least 10 characters.")],
    )

    def validate_news_text(self, field):
        # Basic guard against obviously malicious payloads slipping through
        # (defense in depth -- Jinja2 autoescaping + parameterized queries
        # already protect against XSS/SQLi, this just rejects junk input).
        stripped = field.data.strip()
        if len(stripped) < 10:
            raise ValidationError("Text is too short to analyze.")


class HistorySearchForm(FlaskForm):
    query = StringField("Search", validators=[Length(max=200)])
