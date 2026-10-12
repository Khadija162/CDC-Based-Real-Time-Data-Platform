CREATE TABLE IF NOT EXISTS public.orders (
  order_id BIGINT PRIMARY KEY,
  customer_code TEXT NOT NULL,
  amount NUMERIC(12,2) NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('created','paid','shipped','cancelled')),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
INSERT INTO public.orders(order_id,customer_code,amount,status) VALUES
(1001,'C001',125.50,'created'),(1002,'C002',80,'created'),(1003,'C003',55.20,'created'),
(1004,'C004',199.99,'created'),(1005,'C005',240,'created'),(1006,'C006',45,'created'),
(1007,'C007',75.90,'created'),(1008,'C008',150,'created'),(1009,'C009',60.50,'created'),
(1010,'C010',310,'created'),(1011,'C011',39.99,'created'),(1012,'C012',99,'created')
ON CONFLICT (order_id) DO NOTHING;
