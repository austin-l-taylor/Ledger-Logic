from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from .models import ChartOfAccounts, JournalEntry

User = get_user_model()


class SignUpForm(UserCreationForm):
    """
    A form for user registration.

    This form inherits from Django's built-in UserCreationForm and adds additional fields for date of birth, security questions, and answers. The security questions are static and their fields are read-only.

    Attributes:
    dob (DateField): The user's date of birth. Required.
    email (EmailField): The user's email. Required.
    question1 (CharField): The first security question. Read-only.
    answer1 (CharField): The answer to the first security question. Required.
    question2 (CharField): The second security question. Read-only.
    answer2 (CharField): The answer to the second security question. Required.

    Meta:
        model (Model): The user model this form is associated with.
        fields (tuple): The fields included in this form.
        labels (dict): Custom labels for the fields.
    """

    dob = forms.DateField(required=True)
    email = forms.EmailField(required=True)
    # Security questions are predefined and cannot be changed by the user (disabled=True)
    question1 = forms.CharField(
        initial="What was the name of your first pet?",
        disabled=True,
        widget=forms.TextInput(attrs={"size": "40"}),
    )
    answer1 = forms.CharField(required=True)
    question2 = forms.CharField(
        initial="What city were you born in?",
        disabled=True,
        widget=forms.TextInput(attrs={"size": "40"}),
    )
    answer2 = forms.CharField(required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "dob",
            "question1",
            "answer1",
            "question2",
            "answer2",
        )
        # Custom labels for a better user experience
        labels = {
            "username": "Your username",
            "first_name": "Your first name",
            "last_name": "Your last name",
            "email": "Your email",
            "password1": "Your password",
            "password2": "Confirm your password",
            "dob": "Your date of birth",
            "question1": "Security question 1",
            "answer1": "Answer to security question 1",
            "question2": "Security question 2",
            "answer2": "Answer to security question 2",
        }

    def save(self, commit=True):
        """
        Saves the form's fields to a user instance.

        This method overrides the save method of the superclass. It first calls the superclass's save method with commit=False, which creates a user instance but doesn't save it to the database. It then sets the additional fields on the user instance, sets the date_joined to the current date and time, and sets the password_expiry to 180 days from now. If commit is True, it saves the user instance to the database.

        Parameters:
        commit (bool): Whether to save the user instance to the database. Default is True.

        Returns:
        User: The user instance.
        """
        user = super().save(commit=False)
        # Manually setting additional fields
        user.dob = self.cleaned_data["dob"]
        user.email = self.cleaned_data["email"]
        # Security questions and answers are directly assigned
        user.question1 = self.cleaned_data["question1"]
        user.answer1 = self.cleaned_data["answer1"]
        user.question2 = self.cleaned_data["question2"]
        user.answer2 = self.cleaned_data["answer2"]
        user.date_joined = datetime.now()
        # Setting password expiry to 180 days from the current date
        user.password_expiry = datetime.now() + timedelta(days=180)

        if commit:
            user.save()
        return user


class ForgotPasswordForm(forms.Form):
    """
    A form for the forgot password process.

    This form includes fields for the username and email.

    Attributes:
    username (CharField): The user's username. Required.
    email (EmailField): The user's email. Required.
    """

    username = forms.CharField(required=True)
    email = forms.EmailField(required=True)


class SecurityQuestionForm(forms.Form):
    """
    A form for the security question verification process.

    This form includes fields for the answers to the security questions.

    Attributes:
    answer1 (CharField): The answer to the first security question. Required.
    answer2 (CharField): The answer to the second security question. Required.
    """

    answer1 = forms.CharField(required=True)
    answer2 = forms.CharField(required=True)

    def check_answers(self, user):
        """
        Checks if the provided answers match the user's answers.

        Parameters:
        user (User): The user to check the answers against.

        Returns:
        bool: True if the provided answers match the user's answers, False otherwise.
        """
        answer1 = self.cleaned_data.get("answer1")
        answer2 = self.cleaned_data.get("answer2")

        # Compares provided answers with the user's stored answers
        return answer1 == user.answer1 and answer2 == user.answer2


class EmailForm(forms.Form):
    """
    A form for sending an email.

    This form includes fields for the subject and message of the email.

    Attributes:
    subject (CharField): The subject of the email. Maximum length is 100 characters.
    message (CharField): The message of the email. Uses a textarea widget.
    """

    subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)


class ChartOfAccountForm(forms.ModelForm):
    """
    The form displayed for the Chart of Accounts.

    This form uses the model ChartOfAccounts from .models

    If we need to remove a field from the table then we can use the exclude attribute and specify the field name like the user_id field in this case.

    """
    class Meta:
        model = ChartOfAccounts
        fields = '__all__'  # Or list specific fields if you don't want to include all
        exclude = ('user_id',)  # Exclude user_id if it's automatically set
        widgets = {
            'date_time_account_added': forms.DateInput(attrs={'type': 'date'}),
        }


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['date', 'account', 'debit', 'credit', 'status']