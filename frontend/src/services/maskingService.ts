// Interface definitions
export interface MaskResponse {
  masked_text: string;
  mapping: Record<string, string>;
}

export interface UnmaskResponse {
  text: string;
}

export interface MappingResponse {
  mapping: Record<string, string>;
}

export interface SensitiveEntity {
  type: string;
  value: string;
}

export interface ValidateSensitiveResponse {
  sensitive: boolean;
  entities: SensitiveEntity[];
}

// Mock API service
class MaskingService {
  private mappings: Record<string, Record<string, string>> = {};
  
  // Sensitive information detection patterns
  private readonly sensitivePatterns = [
    // Personal names
    { regex: /\b[A-Z][a-z]+ [A-Z][a-z]+\b/g, type: 'PERSON' },
    // Email addresses
    { regex: /\b[\w.-]+@[\w.-]+\.\w+\b/g, type: 'EMAIL' },
    // Phone numbers (simple pattern)
    { regex: /\b(\+\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b/g, type: 'PHONE' },
    // Credit card numbers (simple pattern)
    { regex: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, type: 'CREDIT_CARD' },
    // Addresses (simple pattern)
    { regex: /\b\d+\s+[A-Za-z\s]+\b,\s*[A-Za-z\s]+\b,\s*[A-Za-z]{2}\s+\d{5}\b/g, type: 'ADDRESS' },
  ];

  // Generate a random token for masking
  private generateToken(type: string): string {
    const prefix = type.charAt(0).toUpperCase() + type.slice(1, 3).toLowerCase();
    const randomId = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
    return `[${prefix}-${randomId}]`;
  }

  // Detect sensitive information in text
  async validateSensitive(text: string): Promise<ValidateSensitiveResponse> {
    // Simulate API delay
    await this.delay(300);
    
    const entities: SensitiveEntity[] = [];
    
    // Check for sensitive information using patterns
    for (const pattern of this.sensitivePatterns) {
      const matches = Array.from(text.matchAll(pattern.regex));
      for (const match of matches) {
        entities.push({
          type: pattern.type,
          value: match[0]
        });
      }
    }
    
    return {
      sensitive: entities.length > 0,
      entities
    };
  }
  
  // Mask sensitive information in text
  async maskText(text: string, chatId: string = 'default'): Promise<MaskResponse> {
    // Simulate API delay
    await this.delay(500);
    
    // Detect sensitive information
    const { entities } = await this.validateSensitive(text);
    
    let maskedText = text;
    const mapping: Record<string, string> = {};
    
    // Replace sensitive information with tokens
    for (const entity of entities) {
      const token = this.generateToken(entity.type);
      maskedText = maskedText.replace(entity.value, token);
      mapping[token] = entity.value;
    }
    
    // Store mapping for this chat
    this.mappings[chatId] = { ...this.mappings[chatId], ...mapping };
    
    return {
      masked_text: maskedText,
      mapping
    };
  }
  
  // Unmask text using the provided mapping
  async unmaskText(maskedText: string, mapping: Record<string, string>): Promise<UnmaskResponse> {
    // Simulate API delay
    await this.delay(300);
    
    let unmaskedText = maskedText;
    
    // Replace tokens with original values
    for (const [token, originalValue] of Object.entries(mapping)) {
      unmaskedText = unmaskedText.replace(token, originalValue);
    }
    
    return {
      text: unmaskedText
    };
  }
  
  // Get mapping for a specific chat
  async getMaskMapping(chatId: string): Promise<MappingResponse> {
    // Simulate API delay
    await this.delay(200);
    
    return {
      mapping: this.mappings[chatId] || {}
    };
  }
  
  // Helper function to simulate API delay
  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Mock examples for testing
  async getMaskingExamples(): Promise<{original: string, masked: string, mapping: Record<string, string>}[]> {
    return [
      {
        original: "My name is John Smith and my email is john.smith@example.com",
        masked: "My name is [Per-1234] and my email is [Ema-5678]",
        mapping: {
          "[Per-1234]": "John Smith",
          "[Ema-5678]": "john.smith@example.com"
        }
      },
      {
        original: "Please call me at 555-123-4567 or visit me at 123 Main St, Springfield, IL 62701",
        masked: "Please call me at [Pho-2345] or visit me at [Add-6789]",
        mapping: {
          "[Pho-2345]": "555-123-4567",
          "[Add-6789]": "123 Main St, Springfield, IL 62701"
        }
      }
    ];
  }
}

export const maskingService = new MaskingService();
