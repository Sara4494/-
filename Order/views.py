from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from Order.serializers import OrderSerializer
from .models import Order
from user.models import CustomUser
from equipment.models import Equipment
from Construction.models import Construction

class CreateOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        item_type = request.data.get('item_type')
        item_id = request.data.get('item_id')

        if not item_type or not item_id:
            return Response({'error': 'item_type و item_id مطلوبين'}, status=400)

        try:
            item_id = int(item_id)
        except ValueError:
            return Response({'error': 'item_id يجب أن يكون رقم صحيح'}, status=400)

        order_data = {
            'buyer': user,
            'item_type': item_type,
            'item_id': item_id,
        }

        
        if item_type == 'worker':
            try:
                worker = CustomUser.objects.get(id=item_id, user_type='worker')
                if worker == user:
                    return Response({'error': 'لا يمكنك إرسال طلب لنفسك'}, status=400)
                order_data['seller'] = worker
                order_data['price'] = worker.price or 0
                order_data['category'] = worker.get_worker_specialization_display() or "عامل"
                order_data['image'] = worker.profile_image
            except CustomUser.DoesNotExist:
                return Response({'error': 'العامل غير موجود'}, status=404)

        elif item_type == 'equipment':
            try:
                equipment = Equipment.objects.get(id=item_id)
                if equipment.owner == user:
                    return Response({'error': 'لا يمكنك إرسال طلب لنفسك'}, status=400)
                order_data['seller'] = equipment.owner
                order_data['price'] = equipment.price
                order_data['category'] = equipment.category.name
                order_data['image'] = equipment.image
            except Equipment.DoesNotExist:
                return Response({'error': 'المعدة غير موجودة'}, status=404)

        elif item_type == 'construction':
            try:
                construction = Construction.objects.get(id=item_id)
                if construction.owner == user:
                    return Response({'error': 'لا يمكنك إرسال طلب لنفسك'}, status=400)
                order_data['seller'] = construction.owner
                order_data['price'] = construction.price
                order_data['category'] = construction.category.name
                order_data['image'] = construction.image
            except Construction.DoesNotExist:
                return Response({'error': 'مواد البناء غير موجودة'}, status=404)

        else:
            return Response({'error': 'نوع العنصر غير صالح'}, status=400)

        order = Order.objects.create(**order_data)

        return Response({
            'message': 'تم إرسال الطلب بنجاح ',
            'order_id': order.id,
            'item_type': order.item_type,
            'category': order.category,
            'price': order.price,
            'created_at': order.created_at,
        }, status=201)



class MyPurchasesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(buyer=request.user)
        data = OrderSerializer(orders, many=True).data
        return Response(data)

class IncomingOrdersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(seller=request.user)
        data = OrderSerializer(orders, many=True).data
        return Response(data)
