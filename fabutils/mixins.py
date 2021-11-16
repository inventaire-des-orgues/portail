import logging

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView, View

logger = logging.getLogger("fabaccess")


class FabSuccessMessageMixin:
    """
    Add a success message on successful form submission.
    """
    success_message = ''

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response


class FabPermissionRequiredMixin(PermissionRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            logger.warning("{user};{method};{get_full_path};403".format(user=request.user,
                                                                        method=request.method,
                                                                        get_full_path=request.get_full_path()))
            return self.handle_no_permission()
        logger.info("{user};{method};{get_full_path};200".format(user=request.user,
                                                                 method=request.method,
                                                                 get_full_path=request.get_full_path()))
        return super().dispatch(request, *args, **kwargs)


class FabCreateView(FabPermissionRequiredMixin, FabSuccessMessageMixin, CreateView):
    pass


class FabUpdateView(FabPermissionRequiredMixin, FabSuccessMessageMixin, UpdateView):
    pass


class FabDeleteView(FabPermissionRequiredMixin, FabSuccessMessageMixin, DeleteView):
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


class FabListView(FabPermissionRequiredMixin, ListView):
    pass


class FabDetailView(FabPermissionRequiredMixin, DetailView):
    pass


class FabView(FabPermissionRequiredMixin, View):
    pass


class JSMixin:
    def handle_no_permission(self):
        return JsonResponse({'message': 'You are not allowed to perform this action', 'errors': []}, status=403)


class FabCreateViewJS(JSMixin, FabPermissionRequiredMixin, CreateView):
    template_name = "no_templates_in_js.html"
    success_message = "Success"

    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse({'message': self.success_message})

    def form_invalid(self, form):
        return JsonResponse({'errors': form.errors.get_json_data(), 'message': 'There is an error in the form'},
                            status=400)


class FabUpdateViewJS(JSMixin, FabPermissionRequiredMixin, UpdateView):
    template_name = "no_templates_in_js.html"
    success_message = "Object modified"

    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse({'message': self.success_message})

    def form_invalid(self, form):
        return JsonResponse({'errors': form.errors.get_json_data(), 'message': 'There is an error in the form'},
                            status=400)


class FabViewJS(JSMixin, FabPermissionRequiredMixin, View):
    pass


class FabDeleteViewJS(JSMixin, FabPermissionRequiredMixin, DeleteView):
    template_name = "no_templates_in_js.html"
    success_message = "Object deleted"

    def delete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'message': self.success_message})
