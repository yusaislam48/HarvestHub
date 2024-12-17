-- ============================
--  Database Setup Script
--  Filename: db_setup.sql
-- ============================

-- 1. Drop existing tables if they exist (optional)
-- Create Database
CREATE DATABASE IF NOT EXISTS harvest_hub;

-- Use the newly created database
USE harvest_hub;

DROP TABLE IF EXISTS transportation_stage, storage_stage, handling_stage, harvesting_stage, harvest_details, farmers, area_officers, crops, region, seasons;

-- 2. Create Tables

-- Area Officers Table
CREATE TABLE area_officers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(15),
    region VARCHAR(255),
    password VARCHAR(255) NOT NULL
);

-- Regions Table
CREATE TABLE region (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region_name VARCHAR(255) NOT NULL UNIQUE
);

-- Crops Table
CREATE TABLE crops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_name VARCHAR(255) NOT NULL,
    crop_id VARCHAR(50) NOT NULL UNIQUE
);

-- Farmers Table
CREATE TABLE farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    address VARCHAR(255),
    region_id INT,
    area DECIMAL(10,2),
    FOREIGN KEY (region_id) REFERENCES region(id)
);

-- Seasons Table
CREATE TABLE seasons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    season_name VARCHAR(255) NOT NULL UNIQUE
);

-- Harvest Details Table
CREATE TABLE harvest_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    harvest_id VARCHAR(255) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    crop_type VARCHAR(255) NOT NULL,
    crop_id VARCHAR(255) NOT NULL,
    season VARCHAR(255) NOT NULL,
    harvest_date DATE NOT NULL,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id)
);

-- Stages Tables: Harvesting, Handling, Storage, Transportation
CREATE TABLE harvesting_stage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    harvest_id INT NOT NULL,
    initial_amount DECIMAL(10,2) NOT NULL,
    remaining_amount DECIMAL(10,2) NOT NULL,
    loss_amount DECIMAL(10,2) NOT NULL,
    loss_percentage DECIMAL(5,2) NOT NULL,
    loss_reason VARCHAR(255)
);

CREATE TABLE handling_stage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    harvest_id INT NOT NULL,
    initial_amount DECIMAL(10,2) NOT NULL,
    remaining_amount DECIMAL(10,2) NOT NULL,
    loss_amount DECIMAL(10,2) NOT NULL,
    loss_percentage DECIMAL(5,2) NOT NULL,
    loss_reason VARCHAR(255)
);

CREATE TABLE storage_stage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    harvest_id INT NOT NULL,
    initial_amount DECIMAL(10,2) NOT NULL,
    remaining_amount DECIMAL(10,2) NOT NULL,
    loss_amount DECIMAL(10,2) NOT NULL,
    loss_percentage DECIMAL(5,2) NOT NULL,
    loss_reason VARCHAR(255)
);

CREATE TABLE transportation_stage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    harvest_id INT NOT NULL,
    initial_amount DECIMAL(10,2) NOT NULL,
    remaining_amount DECIMAL(10,2) NOT NULL,
    loss_amount DECIMAL(10,2) NOT NULL,
    loss_percentage DECIMAL(5,2) NOT NULL,
    loss_reason VARCHAR(255)
);

-- 3. Insert Data

-- Insert into area_officers
INSERT INTO area_officers (name, email, phone, region, password)
VALUES 
('John Doe', 'john@example.com', '1234567890', 'North Region', 'password123'),
('Jane Smith', 'jane@example.com', '0987654321', 'East Region', 'password456');

-- Insert into regions
INSERT INTO region (region_name)
VALUES ('North Region'), ('East Region'), ('West Region'), ('South Region');

-- Insert into crops
INSERT INTO crops (crop_name, crop_id)
VALUES ('Wheat', 'C001'), ('Rice', 'C002'), ('Corn', 'C003'), ('Barley', 'C004');

-- Insert into farmers
INSERT INTO farmers (name, phone, address, region_id, area)
VALUES 
('Farmer A', '1111111111', 'Village A', 1, 10.50),
('Farmer B', '2222222222', 'Village B', 2, 15.75),
('Farmer C', '3333333333', 'Village C', 3, 12.00);

-- Insert into seasons
INSERT INTO seasons (season_name)
VALUES ('Summer'), ('Winter'), ('Spring'), ('Autumn');

-- Insert into harvest_details
INSERT INTO harvest_details (farmer_id, harvest_id, amount, crop_type, crop_id, season, harvest_date)
VALUES 
(1, 'H001', 500.00, 'Wheat', 'C001', 'Summer', '2024-06-01'),
(2, 'H002', 400.00, 'Rice', 'C002', 'Winter', '2024-11-15');

-- Insert into harvesting_stage
INSERT INTO harvesting_stage (farmer_id, harvest_id, initial_amount, remaining_amount, loss_amount, loss_percentage, loss_reason)
VALUES 
(1, 1, 500.00, 450.00, 50.00, 10.00, 'Pests'),
(2, 2, 400.00, 370.00, 30.00, 7.50, 'Adverse Weather');

-- Insert into handling_stage
INSERT INTO handling_stage (farmer_id, harvest_id, initial_amount, remaining_amount, loss_amount, loss_percentage, loss_reason)
VALUES 
(1, 1, 450.00, 430.00, 20.00, 4.44, 'Poor Handling'),
(2, 2, 370.00, 360.00, 10.00, 2.70, 'Transportation Issues');

-- Insert into storage_stage
INSERT INTO storage_stage (farmer_id, harvest_id, initial_amount, remaining_amount, loss_amount, loss_percentage, loss_reason)
VALUES 
(1, 1, 430.00, 420.00, 10.00, 2.33, 'Lack of Storage'),
(2, 2, 360.00, 355.00, 5.00, 1.39, 'Packaging Issues');

-- Insert into transportation_stage
INSERT INTO transportation_stage (farmer_id, harvest_id, initial_amount, remaining_amount, loss_amount, loss_percentage, loss_reason)
VALUES 
(1, 1, 420.00, 410.00, 10.00, 2.38, 'Poor Roads'),
(2, 2, 355.00, 350.00, 5.00, 1.41, 'Theft');
