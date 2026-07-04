-- CRUX — FINAL reset. Safe to run repeatedly. Run the WHOLE thing, once.

-- 1) Clean slate (guaranteed — no leftover rows, no duplicate errors)
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON SCHEMA public TO postgres, service_role;

-- 2) Tables in the app's exact plain-text format
CREATE TABLE account_managers (
	id VARCHAR(36) NOT NULL, 
	name VARCHAR(180) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	title VARCHAR(120) NOT NULL, 
	avatar_url VARCHAR(500), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);
CREATE TABLE announcements (
	id VARCHAR(36) NOT NULL, 
	title VARCHAR(240) NOT NULL, 
	message TEXT NOT NULL, 
	created_by VARCHAR(120), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);
CREATE TABLE users (
	id VARCHAR(36) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	username VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(16) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	last_login_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email), 
	UNIQUE (username)
);
CREATE TABLE audit_logs (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36), 
	action VARCHAR(120) NOT NULL, 
	entity VARCHAR(60), 
	entity_id VARCHAR(60), 
	ip VARCHAR(60), 
	meta JSON, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE clients (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	company_name VARCHAR(200) NOT NULL, 
	contact_name VARCHAR(200) NOT NULL, 
	plan VARCHAR(60) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	currency VARCHAR(8) NOT NULL, 
	timezone VARCHAR(60) NOT NULL, 
	logo_url VARCHAR(500), 
	monthly_budget FLOAT NOT NULL, 
	monthly_target_revenue FLOAT NOT NULL, 
	monthly_target_roas FLOAT NOT NULL, 
	monthly_target_leads INTEGER NOT NULL, 
	account_manager_id VARCHAR(36), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(account_manager_id) REFERENCES account_managers (id)
);
CREATE TABLE ai_insights (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	title VARCHAR(240) NOT NULL, 
	body TEXT NOT NULL, 
	category VARCHAR(20) NOT NULL, 
	impact VARCHAR(10) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE alerts (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	type VARCHAR(30) NOT NULL, 
	severity VARCHAR(10) NOT NULL, 
	title VARCHAR(240) NOT NULL, 
	message TEXT NOT NULL, 
	resolved BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE analytics_snapshots (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	date DATE NOT NULL, 
	visitors INTEGER NOT NULL, 
	sessions INTEGER NOT NULL, 
	bounce_rate FLOAT NOT NULL, 
	engagement_time FLOAT NOT NULL, 
	organic INTEGER NOT NULL, 
	paid INTEGER NOT NULL, 
	direct INTEGER NOT NULL, 
	referral INTEGER NOT NULL, 
	top_countries JSON, 
	top_cities JSON, 
	devices JSON, 
	browsers JSON, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_analytics_client_date UNIQUE (client_id, date), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE campaigns (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	external_id VARCHAR(120), 
	name VARCHAR(200) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	objective VARCHAR(60) NOT NULL, 
	spend FLOAT NOT NULL, 
	reach INTEGER NOT NULL, 
	frequency FLOAT NOT NULL, 
	ctr FLOAT NOT NULL, 
	clicks INTEGER NOT NULL, 
	impressions INTEGER NOT NULL, 
	cpm FLOAT NOT NULL, 
	cpa FLOAT NOT NULL, 
	conversions INTEGER NOT NULL, 
	purchase_roas FLOAT NOT NULL, 
	revenue FLOAT NOT NULL, 
	is_winning BOOLEAN NOT NULL, 
	is_losing BOOLEAN NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE chat_messages (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	sender_id VARCHAR(36) NOT NULL, 
	sender_role VARCHAR(16) NOT NULL, 
	body TEXT NOT NULL, 
	read_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE, 
	FOREIGN KEY(sender_id) REFERENCES users (id)
);
CREATE TABLE documents (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	name VARCHAR(240) NOT NULL, 
	category VARCHAR(16) NOT NULL, 
	file_type VARCHAR(30) NOT NULL, 
	file_url VARCHAR(500) NOT NULL, 
	size_bytes INTEGER NOT NULL, 
	uploaded_by VARCHAR(120), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE goals (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	type VARCHAR(12) NOT NULL, 
	label VARCHAR(160) NOT NULL, 
	target FLOAT NOT NULL, 
	current FLOAT NOT NULL, 
	unit VARCHAR(16) NOT NULL, 
	period VARCHAR(16) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE integrations (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	type VARCHAR(24) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	external_id VARCHAR(200), 
	account_name VARCHAR(200), 
	config JSON, 
	last_synced_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_integration_client_type UNIQUE (client_id, type), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE meeting_notes (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	title VARCHAR(240) NOT NULL, 
	notes TEXT NOT NULL, 
	action_items JSON, 
	recording_url VARCHAR(500), 
	meeting_date TIMESTAMP WITH TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE metric_snapshots (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	date DATE NOT NULL, 
	revenue FLOAT NOT NULL, 
	orders INTEGER NOT NULL, 
	ad_spend FLOAT NOT NULL, 
	roas FLOAT NOT NULL, 
	ctr FLOAT NOT NULL, 
	cpa FLOAT NOT NULL, 
	cpm FLOAT NOT NULL, 
	conversion_rate FLOAT NOT NULL, 
	aov FLOAT NOT NULL, 
	revenue_growth FLOAT NOT NULL, 
	sessions INTEGER NOT NULL, 
	returning_customers INTEGER NOT NULL, 
	new_customers INTEGER NOT NULL, 
	profit_estimate FLOAT NOT NULL, 
	lead_count INTEGER NOT NULL, 
	whatsapp_leads INTEGER NOT NULL, 
	phone_calls INTEGER NOT NULL, 
	impressions INTEGER NOT NULL, 
	clicks INTEGER NOT NULL, 
	reach INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_metric_client_date UNIQUE (client_id, date), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE notifications (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	type VARCHAR(30) NOT NULL, 
	title VARCHAR(240) NOT NULL, 
	message TEXT NOT NULL, 
	read BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE orders (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	external_id VARCHAR(120), 
	order_number VARCHAR(60) NOT NULL, 
	customer_name VARCHAR(200) NOT NULL, 
	total FLOAT NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	items_count INTEGER NOT NULL, 
	source VARCHAR(30) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE performance_scores (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	date DATE NOT NULL, 
	overall INTEGER NOT NULL, 
	ads_score INTEGER NOT NULL, 
	seo_score INTEGER NOT NULL, 
	website_score INTEGER NOT NULL, 
	revenue_score INTEGER NOT NULL, 
	speed_score INTEGER NOT NULL, 
	conversion_score INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_score_client_date UNIQUE (client_id, date), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE products (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	external_id VARCHAR(120), 
	title VARCHAR(240) NOT NULL, 
	category VARCHAR(120) NOT NULL, 
	price FLOAT NOT NULL, 
	units_sold INTEGER NOT NULL, 
	revenue FLOAT NOT NULL, 
	inventory INTEGER NOT NULL, 
	low_stock BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE reports (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	title VARCHAR(240) NOT NULL, 
	month VARCHAR(20) NOT NULL, 
	summary TEXT NOT NULL, 
	wins JSON, 
	losses JSON, 
	kpis JSON, 
	suggestions JSON, 
	strategy TEXT, 
	file_url VARCHAR(500), 
	created_by VARCHAR(120), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE search_console_snapshots (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	date DATE NOT NULL, 
	clicks INTEGER NOT NULL, 
	impressions INTEGER NOT NULL, 
	avg_position FLOAT NOT NULL, 
	ctr FLOAT NOT NULL, 
	top_keywords JSON, 
	top_pages JSON, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_gsc_client_date UNIQUE (client_id, date), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE seo_snapshots (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	date DATE NOT NULL, 
	keyword_growth FLOAT NOT NULL, 
	backlinks INTEGER NOT NULL, 
	indexed_pages INTEGER NOT NULL, 
	technical_issues INTEGER NOT NULL, 
	suggestions JSON, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_seo_client_date UNIQUE (client_id, date), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE tasks (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	title VARCHAR(240) NOT NULL, 
	description TEXT, 
	status VARCHAR(16) NOT NULL, 
	priority VARCHAR(10) NOT NULL, 
	due_date TIMESTAMP WITH TIME ZONE, 
	responsible VARCHAR(120), 
	expected_result VARCHAR(400), 
	timeframe VARCHAR(12) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE tickets (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	subject VARCHAR(240) NOT NULL, 
	description TEXT NOT NULL, 
	priority VARCHAR(10) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE website_health (
	id VARCHAR(36) NOT NULL, 
	client_id VARCHAR(36) NOT NULL, 
	date DATE NOT NULL, 
	performance INTEGER NOT NULL, 
	accessibility INTEGER NOT NULL, 
	seo INTEGER NOT NULL, 
	best_practices INTEGER NOT NULL, 
	lcp FLOAT NOT NULL, 
	fid FLOAT NOT NULL, 
	cls FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_health_client_date UNIQUE (client_id, date), 
	FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE
);
CREATE TABLE ticket_messages (
	id VARCHAR(36) NOT NULL, 
	ticket_id VARCHAR(36) NOT NULL, 
	sender_id VARCHAR(36) NOT NULL, 
	body TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(ticket_id) REFERENCES tickets (id) ON DELETE CASCADE, 
	FOREIGN KEY(sender_id) REFERENCES users (id)
);

-- 3) Your logins
INSERT INTO users (id,email,username,password_hash,role,is_active,created_at,updated_at) VALUES
  ('07508fa5-199b-41a1-b19a-3a454db8639d','[email protected]','Dizigroww','$2b$12$iUuIOvvdmaYjc8iWw6PbeeuX5G3QaC8feqETeEh3Abvge9mAQ2AtK','ADMIN',true,now(),now()),
  ('73dc49b0-aebf-4a7d-97dd-013a0b7a6e0d','[email protected]','admin','$2b$12$M7.Rhw.lzovuGDT.sxCzJ.BmfqBrrR8.FW25nhWQX0qJXIgoSiQam','ADMIN',true,now(),now()),
  ('ba89efb5-bb64-42ce-923a-6764c8b0d79a','[email protected]','aryan','$2b$12$rZbwTLdnfJCbJih6qHqYXONzSx9Mc0BfISUoq7dDci1N9.bivQTrO','CLIENT',true,now(),now());
INSERT INTO clients (id,user_id,company_name,contact_name,plan,status,currency,timezone,monthly_budget,monthly_target_revenue,monthly_target_roas,monthly_target_leads,created_at,updated_at) VALUES
  ('fd0480aa-23aa-4fd5-bdc6-5086a7b64811','ba89efb5-bb64-42ce-923a-6764c8b0d79a','Makhana Mix','Aryan','Growth','ACTIVE','INR','Asia/Kolkata',0,0,0,0,now(),now());