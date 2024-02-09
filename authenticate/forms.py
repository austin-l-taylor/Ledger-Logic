from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

User = get_user_model()

class SignUpForm(UserCreationForm):
    dob = forms.DateField(required=True)
    email = forms.EmailField(required=True)
    question1 = forms.ChoiceField(choices=[('q1', 'Question 1'), ('q2', 'Question 2'), ('q3', 'Question 3')])
    answer1 = forms.CharField(required=True)
    question2 = forms.ChoiceField(choices=[('q1', 'Question 1'), ('q2', 'Question 2'), ('q3', 'Question 3')])
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

    def save(self, commit=True):
        user = super().save(commit=False)
        user.dob = self.cleaned_data["dob"]
        user.email = self.cleaned_data["email"]
        user.question1 = self.cleaned_data["question1"]
        user.answer1 = self.cleaned_data["answer1"]
        user.question2 = self.cleaned_data["question2"]
        user.answer2 = self.cleaned_data["answer2"]
        user.date_joined = datetime.now()
        user.password_expiry = datetime.now() + timedelta(days=180)
        
        if commit:
            user.save()
        return user
