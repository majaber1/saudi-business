-- FeasibilityOS AI - Core Schema (V1)
-- Matches the entity list in README.md section 8.

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'entrepreneur', -- entrepreneur|consultant|investor|government|admin
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50), -- company|consultancy|investor|government
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    organization_id INT REFERENCES organizations(id),
    owner_id INT REFERENCES users(id),
    name VARCHAR(200) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    stage VARCHAR(50) NOT NULL DEFAULT 'idea', -- idea|mvp|early_revenue|growth
    investment NUMERIC(14, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE feasibility_studies (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL, -- general|financial|technical|market|...
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE ai_tasks (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    agent VARCHAR(100) NOT NULL, -- ai_ceo|market|financial|risk|funding|document
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    output JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE financial_models (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    discount_rate NUMERIC(5, 4) NOT NULL DEFAULT 0.10,
    annual_cash_flows NUMERIC(14, 2)[] NOT NULL,
    roi_percent NUMERIC(8, 2),
    payback_years NUMERIC(6, 2),
    npv NUMERIC(16, 2),
    irr_percent NUMERIC(8, 2),
    verdict VARCHAR(30), -- feasible|not_feasible|borderline
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE funding_programs (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL, -- NTDP|MONSHAAT|CODE|SVC|KAFALAH|RDIA
    name VARCHAR(200) NOT NULL,
    description TEXT
);

CREATE TABLE funding_matches (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    funding_program_id INT REFERENCES funding_programs(id),
    score_percent NUMERIC(5, 2) NOT NULL,
    reasons JSONB,
    missing JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL, -- feasibility_study|business_plan|pitch_deck|investor_memo
    file_url TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE knowledge_sources (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    category VARCHAR(100), -- regulation|government_program|benchmark|market_data|investment_info
    source_url TEXT,
    ingested_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE investors (
    id SERIAL PRIMARY KEY,
    organization_id INT REFERENCES organizations(id),
    focus_industries TEXT[],
    ticket_size_min NUMERIC(14, 2),
    ticket_size_max NUMERIC(14, 2),
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    action VARCHAR(200) NOT NULL,
    entity_type VARCHAR(100),
    entity_id INT,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_projects_industry ON projects(industry);
CREATE INDEX idx_ai_tasks_project ON ai_tasks(project_id);
CREATE INDEX idx_funding_matches_project ON funding_matches(project_id);
