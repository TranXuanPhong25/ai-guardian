// Define basic message interface with file attachments
export interface MessageWithFiles {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'function' | 'data' | 'tool';
  content: string;
  createdAt?: Date;
  name?: string;
  function_call?: any;
  tool_calls?: any;
  attached_files?: {
    file_id: number;
    filename: string;
    file_path: string;
  }[];
}

export interface ChatHandler {
  messages: MessageWithFiles[];
  input: string;
  isLoading: boolean;
  handleSubmit: (
    e:
      | React.FormEvent<HTMLFormElement>
      | React.KeyboardEvent<HTMLTextAreaElement>,
    ops?: {
      data?: any;
    }
  ) => void;
  handleInputChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  reload?: () => void;
  stop?: () => void;
  onFileUpload?: (file: File) => Promise<void>;
  onFileError?: (errMsg: string) => void;
  setInput?: (input: string) => void;
  append?: (
    message: MessageWithFiles | Omit<MessageWithFiles, 'id'>,
    ops?: {
      data: any;
    }
  ) => Promise<string | null | undefined>;
}

export interface IChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ILLMModel {
  id: string;
  name: string;
}
