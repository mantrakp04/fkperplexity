import { VapiClient } from "@vapi-ai/web";

// DS-160 Data Structure based on your existing Python structure
export interface DS160Data {
  // Personal Information
  fullName: string;
  gender: 'Male' | 'Female';
  maritalStatus: 'Single' | 'Married' | 'Divorced' | 'Widowed' | 'Separated';
  dateOfBirth: string;
  cityOfBirth: string;
  countryOfBirth: string;
  nationality: string;
  
  // Passport Information
  passportNumber: string;
  passportBookNumber?: string;
  issuingCountry: string;
  placeOfIssue: string;
  dateOfIssue: string;
  expirationDate: string;
  
  // Travel Information
  purposeOfTrip: 'Business' | 'Tourism' | 'Transit' | 'Study' | 'Work' | 'Other';
  intendedDateOfArrival: string;
  intendedLengthOfStay: string;
  usAddress: string;
  personPayingForTrip: 'Self' | 'Other Person/Company' | 'Other';
  
  // U.S. Contact Information
  contactPerson: string;
  contactAddress: string;
  contactPhone: string;
  contactEmail: string;
  
  // Family Information
  fatherName: string;
  motherName: string;
  spouseName?: string;
  
  // Work/Education Information
  primaryOccupation: string;
  employer: string;
  employerAddress: string;
  monthlyIncome: string;
  
  // Security Questions (simplified for voice collection)
  hasBeenArrested: boolean;
  belongsToClanOrTribe: boolean;
  hasSpecializedSkills: boolean;
  hasBeenInvolvedInTerrorism: boolean;
}

// Vapi Agent Configuration
export class DS160VapiAgent {
  private vapi: VapiClient;
  private collectedData: Partial<DS160Data> = {};
  
  constructor(publicKey: string) {
    this.vapi = new VapiClient({
      publicKey,
      apiUrl: "https://api.vapi.ai",
    });
  }

  // Create the DS-160 collection assistant
  createAssistant() {
    return {
      model: {
        provider: "openai",
        model: "gpt-4",
        temperature: 0.7,
        maxTokens: 250,
      },
      voice: {
        provider: "11labs",
        voiceId: "21m00Tcm4TlvDq8ikWAM", // Rachel voice - professional and clear
      },
      name: "DS-160 Assistant",
      firstMessage: "Hi! I'm here to help you complete your DS-160 visa application form through our conversation. I'll ask you a series of questions to gather all the necessary information. This will take about 10-15 minutes. Are you ready to begin?",
      systemPrompt: `You are a professional DS-160 visa application assistant. Your job is to collect all necessary information for a DS-160 form in a natural, conversational manner.

COLLECTION REQUIREMENTS:
You must collect the following information systematically:

1. PERSONAL INFORMATION:
   - Full name (first, middle, last)
   - Gender
   - Marital status
   - Date of birth (MM/DD/YYYY format)
   - City and country of birth
   - Nationality

2. PASSPORT INFORMATION:
   - Passport number
   - Passport book number (if available)
   - Issuing country
   - Place of issue
   - Issue date and expiration date

3. TRAVEL INFORMATION:
   - Purpose of trip to the US
   - Intended arrival date
   - Length of stay
   - US address where you'll stay
   - Who is paying for your trip

4. US CONTACT INFORMATION:
   - Contact person in the US (name, address, phone, email)

5. FAMILY INFORMATION:
   - Father's full name
   - Mother's full name
   - Spouse's name (if married)

6. WORK INFORMATION:
   - Current occupation
   - Employer name and address
   - Monthly income

7. SECURITY QUESTIONS:
   - Have you ever been arrested or convicted of a crime?
   - Do you belong to a clan or tribe?
   - Do you have specialized skills or training in explosives, firearms, or other weapons?
   - Have you ever been involved in terrorist activities?

CONVERSATION STYLE:
- Be professional but friendly and conversational
- Ask one question at a time, don't overwhelm the user
- Confirm important information by repeating it back
- If something is unclear, ask for clarification
- Use natural transitions between topics
- Be patient and understanding - visa applications can be stressful
- If user seems confused about a question, provide brief context about why it's needed

DATA VALIDATION:
- Ensure dates are in correct format
- Verify passport numbers follow reasonable patterns
- Confirm email addresses and phone numbers
- Double-check critical information like names and dates

COMPLETION:
When you have collected all required information, summarize what you've gathered and ask the user to confirm everything is correct before ending the conversation. Then say: "Thank you! I've collected all the information needed for your DS-160 application. This data will now be securely saved to process your application. Have a great day!"

Remember: Be thorough but efficient. The user's time is valuable, but accuracy is crucial for visa applications.`,
      
      // Function calling for data collection
      functions: [
        {
          name: "save_personal_info",
          description: "Save personal information collected from user",
          parameters: {
            type: "object",
            properties: {
              fullName: { type: "string" },
              gender: { type: "string", enum: ["Male", "Female"] },
              maritalStatus: { type: "string", enum: ["Single", "Married", "Divorced", "Widowed", "Separated"] },
              dateOfBirth: { type: "string" },
              cityOfBirth: { type: "string" },
              countryOfBirth: { type: "string" },
              nationality: { type: "string" }
            },
            required: ["fullName", "gender", "maritalStatus", "dateOfBirth", "cityOfBirth", "countryOfBirth", "nationality"]
          }
        },
        {
          name: "save_passport_info",
          description: "Save passport information",
          parameters: {
            type: "object",
            properties: {
              passportNumber: { type: "string" },
              passportBookNumber: { type: "string" },
              issuingCountry: { type: "string" },
              placeOfIssue: { type: "string" },
              dateOfIssue: { type: "string" },
              expirationDate: { type: "string" }
            },
            required: ["passportNumber", "issuingCountry", "placeOfIssue", "dateOfIssue", "expirationDate"]
          }
        },
        {
          name: "save_travel_info",
          description: "Save travel information",
          parameters: {
            type: "object",
            properties: {
              purposeOfTrip: { type: "string", enum: ["Business", "Tourism", "Transit", "Study", "Work", "Other"] },
              intendedDateOfArrival: { type: "string" },
              intendedLengthOfStay: { type: "string" },
              usAddress: { type: "string" },
              personPayingForTrip: { type: "string" }
            },
            required: ["purposeOfTrip", "intendedDateOfArrival", "intendedLengthOfStay", "usAddress", "personPayingForTrip"]
          }
        },
        {
          name: "save_contact_info",
          description: "Save US contact information",
          parameters: {
            type: "object",
            properties: {
              contactPerson: { type: "string" },
              contactAddress: { type: "string" },
              contactPhone: { type: "string" },
              contactEmail: { type: "string" }
            },
            required: ["contactPerson", "contactAddress", "contactPhone", "contactEmail"]
          }
        },
        {
          name: "save_family_info",
          description: "Save family information",
          parameters: {
            type: "object",
            properties: {
              fatherName: { type: "string" },
              motherName: { type: "string" },
              spouseName: { type: "string" }
            },
            required: ["fatherName", "motherName"]
          }
        },
        {
          name: "save_work_info",
          description: "Save work/employment information",
          parameters: {
            type: "object",
            properties: {
              primaryOccupation: { type: "string" },
              employer: { type: "string" },
              employerAddress: { type: "string" },
              monthlyIncome: { type: "string" }
            },
            required: ["primaryOccupation", "employer", "employerAddress", "monthlyIncome"]
          }
        },
        {
          name: "save_security_info",
          description: "Save security background information",
          parameters: {
            type: "object",
            properties: {
              hasBeenArrested: { type: "boolean" },
              belongsToClanOrTribe: { type: "boolean" },
              hasSpecializedSkills: { type: "boolean" },
              hasBeenInvolvedInTerrorism: { type: "boolean" }
            },
            required: ["hasBeenArrested", "belongsToClanOrTribe", "hasSpecializedSkills", "hasBeenInvolvedInTerrorism"]
          }
        },
        {
          name: "complete_collection",
          description: "Mark data collection as complete and prepare for database save",
          parameters: {
            type: "object",
            properties: {
              confirmed: { type: "boolean" },
              summary: { type: "string" }
            },
            required: ["confirmed", "summary"]
          }
        }
      ],

      // End call functionality
      endCallFunctionEnabled: true,
      endCallMessage: "Thank you for providing all the information for your DS-160 application. Your data has been collected and will be processed securely. Good luck with your visa application!",
      
      // Call settings
      maxDurationSeconds: 1800, // 30 minutes max
      silenceTimeoutSeconds: 30,
      recordingEnabled: true,
    };
  }

  // Start a call with the DS-160 assistant
  async startCall(): Promise<string> {
    try {
      const assistant = this.createAssistant();
      
      const call = await this.vapi.start({
        assistant,
      });

      return call.id;
    } catch (error) {
      console.error("Error starting call:", error);
      throw error;
    }
  }

  // Handle function calls from the assistant
  handleFunctionCall(functionName: string, parameters: any) {
    switch (functionName) {
      case 'save_personal_info':
        Object.assign(this.collectedData, parameters);
        console.log('Personal info saved:', parameters);
        break;
      
      case 'save_passport_info':
        Object.assign(this.collectedData, parameters);
        console.log('Passport info saved:', parameters);
        break;
        
      case 'save_travel_info':
        Object.assign(this.collectedData, parameters);
        console.log('Travel info saved:', parameters);
        break;
        
      case 'save_contact_info':
        Object.assign(this.collectedData, parameters);
        console.log('Contact info saved:', parameters);
        break;
        
      case 'save_family_info':
        Object.assign(this.collectedData, parameters);
        console.log('Family info saved:', parameters);
        break;
        
      case 'save_work_info':
        Object.assign(this.collectedData, parameters);
        console.log('Work info saved:', parameters);
        break;
        
      case 'save_security_info':
        Object.assign(this.collectedData, parameters);
        console.log('Security info saved:', parameters);
        break;
        
      case 'complete_collection':
        console.log('Data collection completed:', this.collectedData);
        // Trigger Convex database save
        this.saveToConvex();
        break;
        
      default:
        console.log('Unknown function call:', functionName, parameters);
    }
  }

  // Save collected data to Convex database
  async saveToConvex() {
    try {
      // This will be implemented once Convex is set up
      console.log('Saving to Convex database:', this.collectedData);
      
      // Make API call to your Convex function
      const response = await fetch('/api/convex/save-ds160', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ds160Data: this.collectedData,
          timestamp: new Date().toISOString(),
          status: 'collected'
        }),
      });

      if (response.ok) {
        console.log('Successfully saved to Convex database');
      } else {
        console.error('Failed to save to Convex database');
      }
    } catch (error) {
      console.error('Error saving to Convex:', error);
    }
  }

  // Get collected data
  getCollectedData(): Partial<DS160Data> {
    return this.collectedData;
  }

  // Clear collected data
  clearData() {
    this.collectedData = {};
  }
}

export default DS160VapiAgent;
