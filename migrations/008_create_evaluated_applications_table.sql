-- Create evaluated_applications table for second stage results
CREATE TABLE IF NOT EXISTS evaluated_applications (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    accepted_1 BOOLEAN NOT NULL,
    accepted_2 BOOLEAN NOT NULL,
    accepted_3 BOOLEAN NOT NULL,
    created TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_evaluated_applications_user_id 
        FOREIGN KEY (user_id) REFERENCES users(user_id) 
        ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_evaluated_applications_user_id ON evaluated_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_evaluated_applications_accepted_1 ON evaluated_applications(accepted_1);
CREATE INDEX IF NOT EXISTS idx_evaluated_applications_accepted_2 ON evaluated_applications(accepted_2);
CREATE INDEX IF NOT EXISTS idx_evaluated_applications_accepted_3 ON evaluated_applications(accepted_3);