from dotenv import load_dotenv
import os
import json
from openai import OpenAI
from pydantic import BaseModel, Field, validator, ValidationError
from typing import Optional
from datetime import datetime

load_dotenv(override=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Simple Pydantic model for song request
class SongRequest(BaseModel):
    """Song request model with Pydantic validation"""
    song_name: str = Field(..., min_length=1, max_length=100, description="Name of the song")
    recipient_name: str = Field(..., min_length=1, max_length=50, description="Name of the recipient")
    free_text: str = Field(..., min_length=1, max_length=500, description="Free text message")
    
    @validator('song_name')
    def song_name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Song name cannot be empty')
        return v.strip()
    
    @validator('recipient_name')
    def recipient_name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Recipient name cannot be empty')
        return v.strip()
    
    @validator('free_text')
    def free_text_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Free text cannot be empty')
        return v.strip()

def parse_song_request(user_input: str) -> dict:
    """
    Parse user input into a song request using OpenAI and Pydantic.
    Returns a dictionary with success status, data, and errors.
    """
    try:
        # Use OpenAI to extract structured data
        extraction_prompt = f"""Extract the following information from this user input and return as JSON:
        - song_name: The name of the song
        - recipient_name: The name of the person to send the song to
        - free_text: The message to include
        
        User input: "{user_input}"
        
        Return only valid JSON with these three fields. If any information is missing, make reasonable assumptions."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a data extraction assistant. Extract song request information and return valid JSON only."
                },
                {
                    "role": "user", 
                    "content": extraction_prompt
                }
            ],
            temperature=0.3,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        raw_data = json.loads(response.choices[0].message.content)
        
        # Create Pydantic model (this will validate the data)
        song_request = SongRequest(**raw_data)
        
        return {
            "success": True,
            "song_request": song_request.dict(),
            "errors": [],
            "raw_data": raw_data
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "song_request": None,
            "errors": [f"JSON parsing error: {str(e)}"],
            "raw_data": None
        }
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            errors.append(f"{field}: {error['msg']}")
        
        return {
            "success": False,
            "song_request": None,
            "errors": errors,
            "raw_data": raw_data if 'raw_data' in locals() else None
        }
    except Exception as e:
        return {
            "success": False,
            "song_request": None,
            "errors": [f"Unexpected error: {str(e)}"],
            "raw_data": None
        }

def parse_multiple_requests(user_inputs: list) -> list:
    """
    Parse multiple user inputs into song requests.
    """
    results = []
    for i, user_input in enumerate(user_inputs, 1):
        print(f"\n📝 Processing {i}: {user_input}")
        result = parse_song_request(user_input)
        result["input"] = user_input
        result["index"] = i
        results.append(result)
        
        if result["success"]:
            print("✅ Success!")
            print(f"Song: {result['song_request']['song_name']}")
            print(f"Recipient: {result['song_request']['recipient_name']}")
            print(f"Message: {result['song_request']['free_text']}")
        else:
            print("❌ Failed!")
            for error in result["errors"]:
                print(f"  - {error}")
        
        print("-" * 30)
    
    return results

def main():
    """Main function to demonstrate simple parsing without tools"""
    
    print("🎵 Simple Pydantic Parse-Only Demo")
    print("=" * 50)
    print("This demonstrates parsing user input into structured data using Pydantic")
    print("No tools - only parsing and validation")
    print("=" * 50)
    
    # Example inputs
    examples = [
        "I want to request Bohemian Rhapsody for John with Happy Birthday message",
        "Send Hotel California to Sarah, tell her I miss her",
        "Request Imagine for Mom, say thanks for everything",
        "Billie Jean for Mike, mention our childhood memories",
        "Stairway to Heaven for Dad, he loves classic rock",
        "Wonderwall to Emma, just say thinking of you"
    ]
    
    print("\n🎯 Processing Examples")
    print("=" * 50)
    
    # Process all examples
    results = parse_multiple_requests(examples)
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print(f"\n📊 Summary: {successful} successful, {failed} failed")
    
    # Show successful results
    if successful > 0:
        print("\n✅ Successful Parsings:")
        for result in results:
            if result["success"]:
                print(f"  {result['index']}. {result['song_request']['song_name']} -> {result['song_request']['recipient_name']}")
    
    # Show failed results
    if failed > 0:
        print("\n❌ Failed Parsings:")
        for result in results:
            if not result["success"]:
                print(f"  {result['index']}. {result['input'][:50]}...")
                for error in result["errors"]:
                    print(f"     - {error}")
    
    # Interactive mode
    print("\n🎯 Interactive Mode - Parse your song request!")
    print("Type 'quit' to exit")
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if user_input:
                result = parse_song_request(user_input)
                
                if result["success"]:
                    print("✅ Parsing successful!")
                    print("🎵 Generated Song Request:")
                    print(json.dumps(result["song_request"], indent=2))
                else:
                    print("❌ Parsing failed!")
                    print("Errors:")
                    for error in result["errors"]:
                        print(f"  - {error}")
                    
                    if result["raw_data"]:
                        print("\nRaw extracted data:")
                        print(json.dumps(result["raw_data"], indent=2))
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
