from django.db import models
from django.db.models import QuerySet
from django.utils import timezone


class SoftDeletionQuerySet(QuerySet):
    def delete(self):
        return super(SoftDeletionQuerySet, self).update(deleted_date=timezone.now())

    def hard_delete(self):
        return super(SoftDeletionQuerySet, self).delete()

    def alive(self):
        return self.filter(deleted_date=None)

    def dead(self):
        return self.exclude(deleted_date=None)


class SoftDeletionManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.deleted = kwargs.pop('deleted', False)
        super(SoftDeletionManager, self).__init__(*args, **kwargs)

    def get_queryset(self):
        if self.deleted:
            return SoftDeletionQuerySet(self.model).exclude(deleted_date=None)
        return SoftDeletionQuerySet(self.model).filter(deleted_date=None)

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class SoftDeletionModel(models.Model):
    """
    Inherit form this model to implement Soft Deletion.
    After that :
    - objects.all() will return all instances except deleted ones
    - all_objects.all() will return everything.
    - object.delete() will save the deleted_date for the object
    - object.hard_delete() will completely remove the object from database

    """
    deleted_date = models.DateTimeField(blank=True, null=True, editable=False)
    objects = SoftDeletionManager()
    objects_deleted = SoftDeletionManager(deleted=True)

    class Meta:
        abstract = True

    def delete(self):
        self.deleted_date = timezone.now()
        self.save()

    def hard_delete(self, *args, **kwargs):
        super(SoftDeletionModel, self).delete(*args, **kwargs)
