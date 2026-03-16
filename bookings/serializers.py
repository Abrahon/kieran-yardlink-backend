
# from decimal import Decimal
# from rest_framework import serializers
# from bookings.models import BookingRequest, BookingRequestItem
# from landscapers.models import Service, Addon
# from profiles.models import ClientProfile
# from property.models import Property

# # class BookingRequestSerializer(serializers.ModelSerializer):
# #     client = serializers.ReadOnlyField(source="client.id")
# #     addons = serializers.PrimaryKeyRelatedField(
# #         many=True,
# #         queryset=Addon.objects.all(),
# #         required=False
# #     )

# #     class Meta:
# #         model = BookingRequest
# #         fields = [
# #             "id",
# #             "client",
# #             "property",
# #             "service",
# #             "description",
# #             "booking_type",
# #             "recurring_day_of_week",
# #             "scheduled_date",
# #             "scheduled_time",
# #             "addons",
# #             "price",
# #             "landscaper",
# #             "status",
# #             "note",
# #             "created_at",
# #             "updated_at"
# #         ]
# #         read_only_fields = [
# #             "id", "client", "landscaper", "price", "status",
# #             "created_at", "updated_at"
# #         ]

# #     def validate(self, attrs):
# #         booking_type = attrs.get("booking_type")
# #         service = attrs.get("service")
# #         description = attrs.get("description")
# #         scheduled_date = attrs.get("scheduled_date")
# #         scheduled_time = attrs.get("scheduled_time")
# #         recurring_day = attrs.get("recurring_day_of_week")

# #         if booking_type in ["one_time", "weekly", "biweekly"] and not service:
# #             raise serializers.ValidationError("Service is required for standard bookings.")

# #         if booking_type == "custom" and not description:
# #             raise serializers.ValidationError("Description is required for custom bookings.")

# #         if booking_type == "one_time" and (not scheduled_date or not scheduled_time):
# #             raise serializers.ValidationError("Scheduled date and time required for one-time bookings.")

# #         if booking_type in ["weekly", "biweekly"] and not recurring_day:
# #             raise serializers.ValidationError("Recurring day is required for weekly/biweekly bookings.")

# #         return attrs


# class BookingRequestItemSerializer(serializers.ModelSerializer):
#     service_name = serializers.CharField(source="service.name", read_only=True)
#     addon_name = serializers.CharField(source="addon.name", read_only=True)

#     class Meta:
#         model = BookingRequestItem
#         fields = [
#             "id",
#             "item_type",
#             "service",
#             "service_name",
#             "addon",
#             "addon_name",
#             "name",
#             "description",
#             "price",
#             "sort_order",
#         ]

#     def validate(self, attrs):
#         item_type = attrs.get("item_type")
#         service = attrs.get("service")
#         addon = attrs.get("addon")
#         name = attrs.get("name")
#         price = attrs.get("price")

#         if item_type == BookingRequestItem.ItemType.STANDARD_SERVICE:
#             if not service:
#                 raise serializers.ValidationError("Standard service item must include a service.")
#             attrs["name"] = service.name
#             attrs["description"] = service.description or ""
#             attrs["price"] = service.base_price or Decimal("0.00")

#         elif item_type == BookingRequestItem.ItemType.ADDON:
#             if not addon:
#                 raise serializers.ValidationError("Addon item must include an addon.")
#             attrs["name"] = addon.name
#             attrs["description"] = addon.description or ""
#             attrs["price"] = addon.price or Decimal("0.00")

#         elif item_type == BookingRequestItem.ItemType.CUSTOM:
#             if not name:
#                 raise serializers.ValidationError("Custom item must include a name.")
#             if price is None:
#                 attrs["price"] = Decimal("0.00")

#         return attrs



# class BookingRequestSerializer(serializers.ModelSerializer):
#     items = BookingRequestItemSerializer(many=True, write_only=True)
#     booking_items = BookingRequestItemSerializer(source="items", many=True, read_only=True)

#     class Meta:
#         model = BookingRequest
#         fields = [
#             "id",
#             "client",
#             "property",
#             "service",
#             "description",
#             "booking_type",
#             "recurring_day_of_week",
#             "scheduled_date",
#             "scheduled_time",
#             "addons",
#             "price",
#             "landscaper",
#             "status",
#             "note",
#             "is_active",
#             "job_created",
#             "items",
#             "booking_items",
#             "created_at",
#             "updated_at",
#         ]
#         read_only_fields = ["status", "job_created", "created_at", "updated_at"]

#     def validate(self, attrs):
#         booking_type = attrs.get("booking_type")
#         service = attrs.get("service")
#         description = attrs.get("description")
#         scheduled_date = attrs.get("scheduled_date")
#         scheduled_time = attrs.get("scheduled_time")
#         recurring_day = attrs.get("recurring_day_of_week")

#         if booking_type == BookingRequest.BookingType.CUSTOM and not description:
#             raise serializers.ValidationError("Custom bookings must include a description.")

#         if booking_type == BookingRequest.BookingType.ONE_TIME:
#             if not scheduled_date or not scheduled_time:
#                 raise serializers.ValidationError("One-time booking requires date and time.")

#         if booking_type in [BookingRequest.BookingType.WEEKLY, BookingRequest.BookingType.BIWEEKLY]:
#             if not recurring_day:
#                 raise serializers.ValidationError("Recurring booking requires recurring_day_of_week.")

#         return attrs

#     def create(self, validated_data):
#         items_data = validated_data.pop("items", [])
#         addons = validated_data.pop("addons", [])

#         booking = BookingRequest.objects.create(**validated_data)

#         if addons:
#             booking.addons.set(addons)

#         for idx, item_data in enumerate(items_data):
#             BookingRequestItem.objects.create(
#                 booking=booking,
#                 sort_order=item_data.get("sort_order", idx),
#                 **item_data,
#             )

#         return booking

#     def update(self, instance, validated_data):
#         items_data = validated_data.pop("items", None)
#         addons = validated_data.pop("addons", None)

#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)

#         instance.save()

#         if addons is not None:
#             instance.addons.set(addons)

#         if items_data is not None:
#             instance.items.all().delete()
#             for idx, item_data in enumerate(items_data):
#                 BookingRequestItem.objects.create(
#                     booking=instance,
#                     sort_order=item_data.get("sort_order", idx),
#                     **item_data,
#                 )

#         return instance
# # booking tem

from decimal import Decimal
from rest_framework import serializers
from bookings.models import BookingRequest, BookingRequestItem
from landscapers.models import Service, Addon

from decimal import Decimal
from rest_framework import serializers
from bookings.models import BookingRequestItem
from landscapers.models import Service, Addon


class BookingRequestItemSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    addon_name = serializers.CharField(source="addon.name", read_only=True)

    class Meta:
        model = BookingRequestItem
        fields = [
            "id",
            "item_type",
            "service",
            "service_name",
            "addon",
            "addon_name",
            "name",
            "description",
            "price",
            "sort_order",
        ]
        extra_kwargs = {
            "name": {"required": False, "allow_blank": True},
            "description": {"required": False, "allow_blank": True, "allow_null": True},
            "price": {"required": False},
            "service": {"required": False, "allow_null": True},
            "addon": {"required": False, "allow_null": True},
            "sort_order": {"required": False},
        }

    def validate(self, attrs):
        item_type = attrs.get("item_type")
        service = attrs.get("service")
        addon = attrs.get("addon")
        name = attrs.get("name")
        price = attrs.get("price")

        if item_type == BookingRequestItem.ItemType.STANDARD_SERVICE:
            if not service:
                raise serializers.ValidationError("Standard service item must include a service.")

            attrs["addon"] = None
            attrs["name"] = service.name
            attrs["description"] = service.description or ""

            if service.pricing_type == Service.PricingType.FIXED:
                attrs["price"] = service.base_price or Decimal("0.00")
            else:
                attrs["price"] = service.min_price or Decimal("0.00")

        elif item_type == BookingRequestItem.ItemType.ADDON:
            if not addon:
                raise serializers.ValidationError("Addon item must include an addon.")

            attrs["service"] = None
            attrs["name"] = addon.name
            attrs["description"] = ""
            attrs["price"] = addon.price or Decimal("0.00")

        elif item_type == BookingRequestItem.ItemType.CUSTOM:
            if not name:
                raise serializers.ValidationError("Custom item must include a name.")

            attrs["service"] = None
            attrs["addon"] = None
            attrs["price"] = price if price is not None else Decimal("0.00")

        else:
            raise serializers.ValidationError("Invalid item_type.")

        return attrs

class BookingRequestSerializer(serializers.ModelSerializer):
    items = BookingRequestItemSerializer(many=True, write_only=True)
    booking_items = BookingRequestItemSerializer(source="items", many=True, read_only=True)

    class Meta:
        model = BookingRequest
        fields = [
            "id",
            "client",
            "property",
            "service",
            "description",
            "booking_type",
            "recurring_day_of_week",
            "scheduled_date",
            "scheduled_time",
            "addons",
            "price",
            "landscaper",
            "status",
            "note",
            "is_active",
            "job_created",
            "items",
            "booking_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "client",
            "price",
            "status",
            "job_created",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        booking_type = attrs.get("booking_type")
        description = attrs.get("description")
        scheduled_date = attrs.get("scheduled_date")
        scheduled_time = attrs.get("scheduled_time")
        recurring_day = attrs.get("recurring_day_of_week")

        raw_items = self.initial_data.get("items", [])

        if not raw_items:
            raise serializers.ValidationError("At least one booking item is required.")

        if booking_type == BookingRequest.BookingType.CUSTOM and not description:
            raise serializers.ValidationError("Custom bookings must include a description.")

        if booking_type == BookingRequest.BookingType.ONE_TIME:
            if not scheduled_date or not scheduled_time:
                raise serializers.ValidationError("One-time booking requires date and time.")

        if booking_type in [BookingRequest.BookingType.WEEKLY, BookingRequest.BookingType.BIWEEKLY]:
            if not recurring_day:
                raise serializers.ValidationError("Recurring booking requires recurring_day_of_week.")

        selected_service_ids = [
            item.get("service")
            for item in raw_items
            if item.get("item_type") == BookingRequestItem.ItemType.STANDARD_SERVICE and item.get("service")
        ]

        selected_addon_ids = [
            item.get("addon")
            for item in raw_items
            if item.get("item_type") == BookingRequestItem.ItemType.ADDON and item.get("addon")
        ]

        if selected_addon_ids and not selected_service_ids:
            raise serializers.ValidationError("Addon cannot be selected without at least one service.")

        if selected_service_ids:
            selected_service_ids = set(selected_service_ids)

            for addon_id in selected_addon_ids:
                try:
                    addon = Addon.objects.get(id=addon_id, is_active=True)
                except Addon.DoesNotExist:
                    raise serializers.ValidationError(f"Addon with id {addon_id} not found.")

                addon_service_ids = set(addon.applicable_services.values_list("id", flat=True))

                if selected_service_ids.isdisjoint(addon_service_ids):
                    raise serializers.ValidationError(
                        f"Addon '{addon.name}' is not applicable to the selected service."
                    )

        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        addons = validated_data.pop("addons", [])

        booking = BookingRequest.objects.create(**validated_data)

        if addons:
            booking.addons.set(addons)

        total_price = Decimal("0.00")

        for idx, item_data in enumerate(items_data):
            item = BookingRequestItem.objects.create(
                booking=booking,
                sort_order=item_data.get("sort_order", idx),
                **item_data,
            )
            total_price += item.price or Decimal("0.00")

        booking.price = total_price
        booking.save(update_fields=["price"])

        return booking

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        addons = validated_data.pop("addons", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if addons is not None:
            instance.addons.set(addons)

        if items_data is not None:
            instance.items.all().delete()

            total_price = Decimal("0.00")

            for idx, item_data in enumerate(items_data):
                item = BookingRequestItem.objects.create(
                    booking=instance,
                    sort_order=item_data.get("sort_order", idx),
                    **item_data,
                )
                total_price += item.price or Decimal("0.00")

            instance.price = total_price
            instance.save(update_fields=["price", "updated_at"])

        return instance