-- Create interview_timeslots table for managing interview scheduling
CREATE TABLE IF NOT EXISTS interview_timeslots (
    id SERIAL PRIMARY KEY,
    department_number INTEGER NOT NULL,
    interview_date DATE NOT NULL,
    start_time TIME NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT FALSE,
    reserved_by BIGINT DEFAULT NULL,
    created TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_interview_timeslots_reserved_by 
        FOREIGN KEY (reserved_by) REFERENCES users(user_id) 
        ON DELETE SET NULL,
    
    CONSTRAINT unique_department_date_time 
        UNIQUE (department_number, interview_date, start_time)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_interview_timeslots_department_date ON interview_timeslots(department_number, interview_date);
CREATE INDEX IF NOT EXISTS idx_interview_timeslots_available ON interview_timeslots(is_available);
CREATE INDEX IF NOT EXISTS idx_interview_timeslots_reserved_by ON interview_timeslots(reserved_by);
CREATE INDEX IF NOT EXISTS idx_interview_timeslots_date_time ON interview_timeslots(interview_date, start_time);