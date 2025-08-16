// Interface definitions matching backend API
export interface MaskRequest {
  session_id: string;
  content: string;
}

export interface MaskResponse {
  masked_text: string;
  mapping: Record<string, string>;
  mapping_id?: string;
}

export interface UnmaskRequest {
  masked_text: string;
  mapping: Record<string, string>;
}

export interface UnmaskResponse {
  text: string;
  error?: string;
}

export interface MappingResponse {
  mapping: Record<string, string>;
}

export interface SensitiveEntity {
  type: string;
  value: string;
}

export interface ValidateSensitiveRequest {
  content: string;
}

export interface ValidateSensitiveResponse {
  alert: string | null;
}

// Real API service
class MaskingService {
  private baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Validate if content contains sensitive information
  async validateSensitive(content: string): Promise<ValidateSensitiveResponse> {
    const response = await fetch(`${this.baseUrl}/mask/validate-sensitive`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
    return response.json();
  }

  // Mask sensitive information in text
  async maskText(sessionId: string, content: string): Promise<MaskResponse> {
    const response = await fetch(`${this.baseUrl}/mask/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, content })
    });
    return response.json();
  }

  // Unmask text using provided mapping
  async unmaskText(maskedText: string, mapping: Record<string, string>): Promise<UnmaskResponse> {
    const response = await fetch(`${this.baseUrl}/mask/unmask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ masked_text: maskedText, mapping })
    });
    return response.json();
  }

  // Get stored mapping for a session
  async getMaskMapping(sessionId: string): Promise<MappingResponse> {
    const response = await fetch(`${this.baseUrl}/mask/mask-mapping/${sessionId}`);
    return response.json();
  }
}

export const maskingService = new MaskingService();
