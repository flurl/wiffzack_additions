use wiffzack
go

-- Drop the function if it already exists to allow for easy updates
IF OBJECT_ID('dbo.getWarengruppe', 'FN') IS NOT NULL
    DROP FUNCTION dbo.getWarengruppe;
GO

-- Create the scalar function without any side-effecting operators
CREATE FUNCTION dbo.getWarengruppe (@inputString NVARCHAR(MAX))
RETURNS NVARCHAR(MAX)
AS
BEGIN
    -- Declare variables
    DECLARE @dollarPos INT;
    DECLARE @lengthString NVARCHAR(MAX);
    DECLARE @length INT;
    DECLARE @result NVARCHAR(MAX);

    -- Find the position of the first '$' delimiter
    SET @dollarPos = CHARINDEX('$', @inputString);

    -- Check for an invalid format. We need at least 'S1$' (3 chars).
    IF @dollarPos < 3
    BEGIN
        RETURN NULL;
    END

    -- Extract the portion of the string that should represent the length
    SET @lengthString = SUBSTRING(@inputString, 2, @dollarPos - 2);

    -- ** SAFE VALIDATION LOGIC FOR SQL SERVER 2008 **
    -- Check if the lengthString is empty or contains any character that is NOT a digit (0-9).
    IF @lengthString = '' OR @lengthString LIKE '%[^0-9]%'
    BEGIN
        -- If it's not a valid integer string, return NULL to indicate a parsing failure.
        SET @result = NULL;
    END
    ELSE
    BEGIN
        -- The string is safe to cast.
        SET @length = CAST(@lengthString AS INT);
        -- Extract the main group name using the starting position and the now-validated length.
        SET @result = SUBSTRING(@inputString, @dollarPos + 1, @length);
    END

    -- Return the final extracted string
    RETURN @result;
END
GO