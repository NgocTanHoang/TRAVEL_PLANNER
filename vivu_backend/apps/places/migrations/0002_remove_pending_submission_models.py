from django.db import migrations


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ("itineraries", "0003_consolidate_ai_and_pending_layers"),
        ("places", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL("DROP TABLE IF EXISTS PENDING_PLACE_IMAGES"),
            ],
            state_operations=[
                migrations.DeleteModel(
                    name="PendingPlaceImage",
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL("DROP TABLE IF EXISTS PENDING_PLACES"),
            ],
            state_operations=[
                migrations.DeleteModel(
                    name="PendingPlace",
                ),
            ],
        ),
    ]
