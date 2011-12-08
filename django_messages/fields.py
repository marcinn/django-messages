"""
Based on http://www.djangosnippets.org/snippets/595/
by sopelkin
"""

from django import forms
from django.forms import widgets
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse


class CommaSeparatedUserInput(widgets.HiddenInput):
    
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        elif isinstance(value, (list, tuple)):
            value = (', '.join([user.username for user in value]))
        return super(CommaSeparatedUserInput, self).render(name, value, attrs)
        


class CommaSeparatedUserField(forms.Field):
    widget = CommaSeparatedUserInput
    
    def __init__(self, *args, **kwargs):
        recipient_filter = kwargs.pop('recipient_filter', None)
        self._recipient_filter = recipient_filter
        super(CommaSeparatedUserField, self).__init__(*args, **kwargs)
        
    def clean(self, value):
        super(CommaSeparatedUserField, self).clean(value)
        if not value:
            return ''
        if isinstance(value, (list, tuple)):
            return value
        
        names = set(value.split(','))
        names_set = set([name.strip() for name in names])
        users = list(User.objects.filter(username__in=names_set))
        unknown_names = names_set ^ set([user.username for user in users])
        
        recipient_filter = self._recipient_filter
        invalid_users = []
        if recipient_filter is not None:
            for r in users:
                if recipient_filter(r) is False:
                    users.remove(r)
                    invalid_users.append(r.username)
        
        if unknown_names or invalid_users:
            raise forms.ValidationError(_(u"The following usernames are incorrect: %(users)s") % {'users': ', '.join(list(unknown_names)+invalid_users)})
        
        return users



class AutocompleteRecipient(widgets.TextInput):
    def render(self, name, value, attrs):
        out = super(AutocompleteRecipient, self).render(name, value, attrs)
        out += """
        <script type="text/javascript">
        $(document).ready(function() {
            var name_obj = $('#%(input_id)s');
            var id_obj = $('#id_recipients');
            $(name_obj).autocomplete({
                source: '%(autocomplete_url)s',
                minLength: 2,
                focus: function(ev,ui) {
                    $(name_obj).val(ui.item.label);
                    return false;
                },
                select: function(ev,ui) {
                    var item=ui.item;
                    $(id_obj).val(item.value);
                    $(name_obj).val(item.label);
                    return false;
                }
            });
        });
        </script>
        """ % {
                'input_id': 'id_%s' % name,
                'autocomplete_url': reverse('messages_recipients_autocomplete'),
                }
        return mark_safe(out)

