from django import forms
from .models import ScrollSession

class ScrollSessionform(forms.ModelForm):
    class Meta:
        model = ScrollSession
        fields = ['app_name', 'duration', 'scroll_count', 'momentum']


    def clean_duration(self):
        duration = self.cleaned_data['duration']

        if duration <= 0:
            raise forms.ValidationError(
                "Duration must be greater than zero."
            )
        if duration > 86400:
            raise forms.ValidationError(
                "Duration cannot exceed 24 hours"
            )

        return duration


    def clean_scroll_count(self):
        scroll_count = self.cleaned_data['scroll_count']

        if scroll_count <= 0:
            raise forms.ValidationError(
                "Scroll count must be greater than zero."
            )

        if scroll_count > 100000:
            raise forms.ValidationError(
                "Scroll count cannot exceed 100,000."
            )

        return scroll_count

    

    def clean_app_name(self):
        app_name = self.cleaned_data['app_name'].strip()

        if not app_name:
            raise forms.ValidationError(
                "Application name cannot be empty."
            )

        if len(app_name) > 50:
            raise forms.ValidationError(
                "Application name cannot exceed 50 characters."
            )

        return app_name

    
    def clean_momentum(self):
        momentum = self.cleaned_data['momentum']

        valid_choices = ['LOW', 'MEDIUM', 'HIGH']

        if momentum not in valid_choices:
            raise forms.ValidationError(
                "Please select a valid momentum level."
            )

        return momentum


