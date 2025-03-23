-- Users Table (Unchanged)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    firstname varchar(50),
    lastname varchar(50),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    department_id INT REFERENCES department(id) ON DELETE CASCADE,
    designation_name VARCHAR(50),
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    first_login_flag BOOLEAN DEFAULT TRUE,
    user_type VARCHAR(20) NOT NULL,
    created_by INT,
    reset_token  VARCHAR(100)  UNIQUE,
    reset_token_expiry = TIMESTAMP 

);

CREATE TABLE department (
    id SERIAL PRIMARY KEY,
    name varchar(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active' 
    

);

CREATE TABLE login_history (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    login_status VARCHAR(20) NOT NULL ,
    latitude DECIMAL(9,6) ,
    longitude DECIMAL(9,6),
    ip_addr VARCHAR(20),
    channel VARCHAR(20),
    device_name VARCHAR(255),
    user_agent TEXT,  
    ip_address VARCHAR(45),
    mac_address VARCHAR(20)
);

-- Categories Table (New)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    status VARCHAR(10) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    thumbnail_url TEXT,  -- URL for category thumbnail
    image_url TEXT,  -- URL for category full image
    created_by INT NOT NULL,  -- User ID of creator
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

    
);

CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    category_id INT REFERENCES categories(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    option_1 TEXT NOT NULL,
    option_2 TEXT NOT NULL,
    option_3 TEXT NOT NULL,
    option_4 TEXT NOT NULL,
    score_1 INT NOT NULL,
    score_2 INT NOT NULL,
    score_3 INT NOT NULL,
    score_4 INT NOT NULL,
    status VARCHAR(10) DEFAULT 'active',
    created_by INT NOT NULL,  -- User ID of creator
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


-- Responses Table (Updated)
CREATE TABLE responses (
    id SERIAL PRIMARY KEY,
    user_id varchar(255) NOT NULL, -- Can repeat for different questions
    question_id INT NOT NULL,
    selected_option VARCHAR(30) NOT NULL, -- Stores the selected option (1-4)
    channel VARCHAR(10) NOT NULL, -- Mobile/Web
    stage VARCHAR(30), -- Optional: Captures when the response was recorded
    dob DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE TABLE risk_profiles (
    id SERIAL PRIMARY KEY,
    profile_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    score_threshold INT NOT NULL CHECK (score_threshold BETWEEN 0 AND 100), -- % Score
    individual_score INT ,
    tags TEXT, -- JSON or comma-separated tags/keywords
    status VARCHAR(10) NOT NULL CHECK (status IN ('active', 'inactive')), -- Profile Status
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


CREATE TABLE user_risk (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL, -- Unique identifier (Frontend generated)
    risk_profile_id INT NOT NULL, -- Mapped to risk_profiles table
    risk_profile_name VARCHAR(255) NOT NULL, -- Derived from risk_profiles table
    risk_score INT NOT NULL CHECK (risk_score BETWEEN 0 AND 100), -- Total score
    channel VARCHAR(10) NOT NULL,
    category_id INT REFERENCES categories(id),
    status VARCHAR(10) NOT NULL CHECK (status IN ('active', 'inactive')), -- Active or Inactive
    user_stars INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_validation VARCHAR(20),
    validated_at TIMESTAMP,
    FOREIGN KEY (risk_profile_id) REFERENCES risk_profiles(id)
    
);

CREATE TABLE menus (
    id SERIAL PRIMARY KEY,
    menu_name VARCHAR(50),
    menu_description text,
    mem_default varchar(5) NOT NULL DEFAULT 'N',
    status VARCHAR(10) NOT NULL DEFAULT 'active', 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    
);

CREATE TABLE user_acl (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    menu_id INT REFERENCES menus(id) ON DELETE CASCADE,
    access_flag VARCHAR(10) NOT NULL DEFAULT 'Y', 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    
    
);

CREATE TABLE organisation (
    id SERIAL PRIMARY KEY,
    org_name VARCHAR(100) ,
    portal_name VARCHAR(100) ,
    logo VARCHAR(255),
    website_url VARCHAR(255),
    mail_server  VARCHAR(255),
    mail_port  INT,
    username  VARCHAR(100),
    password_hash  VARCHAR(100),
    smtp_server  VARCHAR(100),
    status VARCHAR(10) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



