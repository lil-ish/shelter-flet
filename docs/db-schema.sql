CREATE TABLE users (
    user_id int generated always as identity primary key,
    full_name TEXT NOT NULL,
    contact_info TEXT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK (role IN ('Директор', 'Сотрудник', 'Администратор', 'Ветеринар', 'Волонтер', 'Попечитель')),
    start_date DATE
);

CREATE TABLE animal (
    animal_id int generated always as identity primary key,
    name TEXT NOT NULL,
    gender TEXT CHECK (gender IN ('кот', 'кошка')),
    health_status TEXT CHECK (health_status IN ('котики-инвалиды', 'требуется лечение', 'хорошее', 'отличное')),
    care_status TEXT CHECK (care_status IN ('доступна', 'под опекой')),
    admission_date DATE,
    birth_date DATE,
    character_description TEXT,
    reason TEXT,
    photo BYTEA
);

CREATE TABLE tasks (
    task_id int generated always as identity primary key,
    description TEXT NOT NULL,
    execution_date DATE,
    status TEXT CHECK (status IN ('выполнено', 'не выполнено')),
    fk_user_id INT REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE fundraising (
    fund_id int generated always as identity primary key,
    goal TEXT NOT NULL,
    description TEXT,
    target_amount NUMERIC(10,2),
    collected_amount NUMERIC(10,2) DEFAULT 0,
    status TEXT CHECK (status IN ('активен', 'завершён')),
    start_date DATE,
    end_date DATE
);

CREATE TABLE donations (
    donat_id int generated always as identity primary key,
    fk_fund_id INT REFERENCES fundraising(fund_id) ON DELETE SET NULL,
    fk_user_id INT REFERENCES users(user_id) ON DELETE SET NULL,
    amount NUMERIC(10,2) NOT NULL,
    payment_date DATE,
    comment TEXT
);

CREATE TABLE subscriptions (
    sub_id int generated always as identity primary key,
    fk_user_id INT UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    start_date DATE,
    cancel_date DATE,
    next_payment_date DATE,
    card_info TEXT,
    amount NUMERIC(10,2)
);

CREATE TABLE reports (
    report_id int generated always as identity primary key,
    publication_date DATE,
    period TEXT CHECK (period IN ('годовой', 'ежемесячный')),
    document_link TEXT,
    fk_user_id INT REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE animal_vet (
    fk_animal_id INT REFERENCES animal(animal_id) ON DELETE CASCADE,
    fk_user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    PRIMARY KEY (fk_animal_id, fk_user_id)
);

CREATE TABLE animal_guardian (
    fk_animal_id INT REFERENCES animal(animal_id) ON DELETE CASCADE,
    fk_user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    PRIMARY KEY (fk_animal_id, fk_user_id)
);

