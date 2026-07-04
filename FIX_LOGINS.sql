-- CRUX — fix logins. SELECT ALL (Cmd/Ctrl+A) then RUN. Safe to re-run.

DELETE FROM clients WHERE company_name = 'Makhana Mix';
DELETE FROM users WHERE username IN ('Dizigroww','admin','aryan')
   OR email IN ('[email protected]','[email protected]','[email protected]');

INSERT INTO users (id,email,username,password_hash,role,is_active,created_at,updated_at) VALUES
  ('ac030a3a-7ec9-4307-84cf-cc7e1dfa08c0','[email protected]','Dizigroww','$2b$12$NULOKqlLmVfJjNyC465BneL0h3SFTQMffHxcXWaicxyfyWUxoFfB2','ADMIN',true,now(),now()),
  ('a873677e-3281-41fb-9f11-b3f95fd8720d','[email protected]','admin','$2b$12$s/ep4m.DlZhvTuQvE7CoGOffPy8eoO3BkVijNYH9SzOvvXdYkIlUO','ADMIN',true,now(),now()),
  ('d515ac14-ec6f-4e03-a3a2-9c93c9a06ba8','[email protected]','aryan','$2b$12$rWMobIR.GrqCTFBd.RnaeOTFVshe8s8M5UK2UyL2SLrKXWI7VYkLC','CLIENT',true,now(),now());

INSERT INTO clients (id,user_id,company_name,contact_name,plan,status,currency,timezone,monthly_budget,monthly_target_revenue,monthly_target_roas,monthly_target_leads,created_at,updated_at) VALUES
  ('f180ef7d-f8f0-41ab-b16a-1507454a3657','d515ac14-ec6f-4e03-a3a2-9c93c9a06ba8','Makhana Mix','Aryan','Growth','ACTIVE','INR','Asia/Kolkata',0,0,0,0,now(),now());
