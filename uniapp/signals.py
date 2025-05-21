from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Post  # adjust import as needed

@receiver(post_delete, sender=Post)
def delete_attached_files(sender, instance, **kwargs):
    if instance.document:
        instance.document.delete(save=False)  # deletes from storage
    if instance.image:
        instance.image.delete(save=False)     # deletes from storage
