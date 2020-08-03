# Generated by Django 2.1.11 on 2020-07-30 10:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("responses", "0010_response_submitted_to_play_store_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="response",
            name="review",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="responses",
                to="reviews.Review",
            ),
        ),
    ]