from django import forms


class Select2Multiple(forms.widgets.SelectMultiple):
    """
    Create html <option></option> only for already selected elements.
    Rest of options will be populated through select2 API.
    """
    def optgroups(self, name, value, attrs=None):
        """Return a list of optgroups for this widget."""
        groups = []
        for index, choice in enumerate(self.choices.queryset.filter(id__in=value)):
            subgroup = []
            group_name = None
            groups.append((group_name, subgroup, index))
            subgroup.append(self.create_option(
                name, choice.id, str(choice), selected=True, index=index, attrs=attrs,
            ))
        return groups

class Select2Single(forms.widgets.Select):
    """
    Create html <option></option> only for already selected elements to save loading time.
    Rest of options will be populated through select2 API.
    """

    def optgroups(self, name, value, attrs=None):
        """Return a list of optgroups for this widget."""
        groups = []
        if len(value) and value[0]:
            option = self.choices.queryset.get(id=value[0])
            groups.append((None,[self.create_option(name,option.id,str(option),selected=True,index=0,attrs=attrs)],0))
        return groups
