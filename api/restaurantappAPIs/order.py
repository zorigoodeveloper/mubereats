class RestaurantConfirmOrderView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        user = request.user

        # 1. Зөвхөн restaurant
        if user['user_type'] != 'restaurant':
            return Response(
                {'error': 'Зөвхөн restaurant захиалга баталгаажуулна'},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Захиалга авах
        order = execute_query(
            """
            SELECT id, restaurant_id, status
            FROM orders
            WHERE id = %s
            """,
            (order_id,),
            fetch_one=True
        )

        if not order:
            return Response(
                {'error': 'Захиалга олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Өөр restaurant-ийн захиалга эсэх
        if order['restaurant_id'] != user['id']:
            return Response(
                {'error': 'Энэ захиалга таных биш'},
                status=status.HTTP_403_FORBIDDEN
            )

        # 4. Status шалгах
        if order['status'] != 'pending':
            return Response(
                {'error': 'Захиалга аль хэдийн шийдэгдсэн'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5. ЗАХИАЛГА БАТАЛГААЖЛАА ✅
        execute_insert(
            """
            UPDATE orders
            SET status = 'confirmed'
            WHERE id = %s
            """,
            (order_id,)
        )

        return Response(
            {'message': 'Захиалга баталгаажлаа'},
            status=status.HTTP_200_OK
        )
