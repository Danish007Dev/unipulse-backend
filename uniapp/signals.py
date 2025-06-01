from django.db.models.signals import post_delete
from django.dispatch import receiver
from uniapp.models import Post
from django.conf import settings
from supabase import create_client

# Setup Supabase client
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_SERVICE_KEY = settings.SUPABASE_SERVICE_KEY
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def extract_supabase_path(url):
    parts = url.split('/media-unipulse/')
    if len(parts) == 2:
        return parts[1]
    return None

@receiver(post_delete, sender=Post)
def delete_post_attachments(sender, instance, **kwargs):
    doc_path = extract_supabase_path(instance.document) if instance.document else None
    img_path = extract_supabase_path(instance.image) if instance.image else None

    if doc_path:
        supabase.storage.from_("media-unipulse").remove([doc_path])
    if img_path:
        supabase.storage.from_("media-unipulse").remove([img_path])
