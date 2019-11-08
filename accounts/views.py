from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.models import Group
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse

from fabutils.mixins import FabListView, FabCreateView, FabUpdateView, FabDeleteView, FabView

User = get_user_model()


class UserList(FabListView):
    """
    Admin only
    List and search all users.
    """
    model = User
    permission_required = 'accounts.view_user'
    paginate_by = 30

    def get_queryset(self):
        queryset = User.objects.all().order_by("last_name")
        query = self.request.GET.get("query")
        group = self.request.GET.get("group")

        if group:
            queryset = Group.objects.get(name=group).user_set.all()
        if query:
            queryset = queryset.filter(
                Q(email__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)).distinct()

        return queryset


class UserCreate(FabCreateView):
    """
    Admin only
    """
    model = User
    permission_required = "accounts.add_user"
    success_message = "User created"
    success_url = reverse_lazy("accounts:user-list")
    fields = ["first_name", "last_name", "email", "password", "groups"]

    def form_valid(self, form):
        user = form.save()
        user.set_password(form.cleaned_data["password"])
        user.save()
        messages.success(self.request, self.success_message)
        return redirect(self.success_url)


class UserUpdate(FabUpdateView):
    """
    Admin only
    """
    model = User
    permission_required = "accounts.change_user"
    slug_field = "uuid"
    slug_url_kwarg = "user_uuid"
    success_message = "User updated"
    success_url = reverse_lazy("accounts:user-list")
    fields = ["first_name", "last_name", "email", "groups"]


class UserDelete(FabDeleteView):
    """
    Admin only
    """
    model = User
    permission_required = "accounts.delete_user"
    slug_field = "uuid"
    slug_url_kwarg = "user_uuid"
    success_message = "User deleted"
    success_url = reverse_lazy("accounts:user-list")


class UserUpdatePassword(FabUpdateView):
    """
    Admin only
    """
    model = User
    permission_required = "accounts.change_user"
    slug_field = "uuid"
    slug_url_kwarg = "user_uuid"
    success_message = "User password updated"
    form_class = AdminPasswordChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = kwargs.pop('instance')
        return kwargs

    def get_success_url(self):
        return reverse('accounts:user-update', args=(self.object.uuid,))



class AccessLogs(FabView):
    permission_required = "accounts.add_user"

    def get(self, request, *args, **kwargs):
        rows = int(request.GET.get("rows",100))
        with open(settings.FABACCESSLOG_FILE) as f:
            reader = csv.reader(deque(f, maxlen=rows), delimiter=";")
            access_logs = list(reader)
        return render(request, "accounts/access_logs.html", {"access_logs": access_logs})
