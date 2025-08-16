export interface SafetyResult {
   isSafe: boolean;
   riskLevel: 'low' | 'medium' | 'high';
   reasons: string[];
   suggestions?: string[];
}

export interface FileAnalysis extends SafetyResult {
   fileType: string;
   fileSize: number;
   fileName: string;
}

export interface MessageAnalysis extends SafetyResult {
   messageLength: number;
   detectedLanguage: string;
}

class SafetyService {
   // Mock patterns để phát hiện nội dung không an toàn
   private readonly dangerousPatterns = [
      // Từ khóa bạo lực
      /\b(kill|murder|weapon|bomb|terrorist|violence)\b/i,
      // Từ khóa độc hại
      /\b(hack|malware|virus|exploit|crack)\b/i,
      // Từ khóa nhạy cảm
      /\b(password|credit card|ssn|social security)\b/i,
      // Từ khóa spam
      /\b(click here|free money|buy now|limited time)\b/i,
   ];

   private readonly suspiciousFileTypes = [
      '.exe', '.bat', '.cmd', '.scr', '.pif', '.com',
      '.jar', '.vbs', '.js', '.jse', '.ws', '.wsf'
   ];

   private readonly riskyFileTypes = [
      '.zip', '.rar', '.7z', '.tar', '.gz'
   ];

   /**
    * Kiểm tra an toàn của message
    */
   async analyzeMessage(message: string): Promise<MessageAnalysis> {
      await this.simulateDelay();

      const dangerousMatches = this.dangerousPatterns.filter(pattern =>
         pattern.test(message)
      );

      let riskLevel: 'low' | 'medium' | 'high' = 'low';
      let reasons: string[] = [];
      let suggestions: string[] = [];

      // Kiểm tra độ dài message
      if (message.length > 5000) {
         riskLevel = 'medium';
         reasons.push('Message quá dài có thể chứa spam');
         suggestions.push('Chia nhỏ message thành nhiều phần');
      }

      // Kiểm tra patterns nguy hiểm
      if (dangerousMatches.length > 0) {
         riskLevel = 'high';
         reasons.push('Phát hiện nội dung có thể không an toàn');
         suggestions.push('Kiểm tra lại nội dung trước khi gửi');
      }

      // Kiểm tra ký tự đặc biệt
      const specialCharCount = (message.match(/[^\w\s]/g) || []).length;
      if (specialCharCount > message.length * 0.3) {
         riskLevel = 'medium';
         reasons.push('Chứa quá nhiều ký tự đặc biệt');
         suggestions.push('Giảm số lượng ký tự đặc biệt');
      }

      // Kiểm tra URL
      const urlPattern = /https?:\/\/[^\s]+/g;
      const urls = message.match(urlPattern);
      if (urls && urls.length > 3) {
         riskLevel = 'medium';
         reasons.push('Chứa nhiều liên kết có thể là spam');
         suggestions.push('Kiểm tra tính hợp lệ của các liên kết');
      }

      return {
         isSafe: riskLevel === 'low',
         riskLevel,
         reasons,
         suggestions,
         messageLength: message.length,
         detectedLanguage: this.detectLanguage(message)
      };
   }

   /**
    * Kiểm tra an toàn của file
    */
   async analyzeFile(file: File): Promise<FileAnalysis> {
      await this.simulateDelay();

      const fileName = file.name.toLowerCase();
      const fileExtension = fileName.substring(fileName.lastIndexOf('.'));

      let riskLevel: 'low' | 'medium' | 'high' = 'low';
      let reasons: string[] = [];
      let suggestions: string[] = [];

      // Kiểm tra loại file nguy hiểm
      if (this.suspiciousFileTypes.some(ext => fileName.endsWith(ext))) {
         riskLevel = 'high';
         reasons.push('Loại file có thể chứa mã độc');
         suggestions.push('Không tải lên file thực thi');
      }

      // Kiểm tra file nén
      if (this.riskyFileTypes.some(ext => fileName.endsWith(ext))) {
         riskLevel = 'medium';
         reasons.push('File nén có thể chứa nội dung không mong muốn');
         suggestions.push('Kiểm tra nội dung file trước khi tải lên');
      }

      // Kiểm tra kích thước file
      const maxSizeInMB = 10;
      const fileSizeInMB = file.size / (1024 * 1024);
      if (fileSizeInMB > maxSizeInMB) {
         riskLevel = riskLevel === 'high' ? 'high' : 'medium';
         reasons.push(`File quá lớn (${fileSizeInMB.toFixed(2)}MB > ${maxSizeInMB}MB)`);
         suggestions.push('Nén file hoặc chia nhỏ file');
      }

      // Kiểm tra tên file đáng ngờ
      if (fileName.includes('..') || fileName.includes('/') || fileName.includes('\\')) {
         riskLevel = 'high';
         reasons.push('Tên file chứa ký tự không hợp lệ');
         suggestions.push('Đổi tên file loại bỏ ký tự đặc biệt');
      }

      return {
         isSafe: riskLevel === 'low',
         riskLevel,
         reasons,
         suggestions,
         fileType: file.type || 'unknown',
         fileSize: file.size,
         fileName: file.name
      };
   }

   /**
    * Kiểm tra an toàn của nhiều file
    */
   async analyzeFiles(files: File[]): Promise<FileAnalysis[]> {
      return Promise.all(files.map(file => this.analyzeFile(file)));
   }

   private detectLanguage(text: string): string {
      // Mock language detection
      const vietnamesePattern = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i;

      if (vietnamesePattern.test(text)) {
         return 'vi';
      }
      return 'en';
   }

   private async simulateDelay(): Promise<void> {
      // Simulate API call delay
      const delay = Math.random() * 500 + 200; // 200-700ms
      return new Promise(resolve => setTimeout(resolve, delay));
   }

   /**
    * Lấy cấp độ màu cho từng risk level
    */
   getRiskColor(riskLevel: 'low' | 'medium' | 'high'): string {
      switch (riskLevel) {
         case 'low':
            return 'text-green-600 dark:text-green-400';
         case 'medium':
            return 'text-yellow-600 dark:text-yellow-400';
         case 'high':
            return 'text-red-600 dark:text-red-400';
         default:
            return 'text-gray-600 dark:text-gray-400';
      }
   }

   /**
    * Lấy icon cho từng risk level
    */
   getRiskIcon(riskLevel: 'low' | 'medium' | 'high'): string {
      switch (riskLevel) {
         case 'low':
            return '✅';
         case 'medium':
            return '⚠️';
         case 'high':
            return '🚨';
         default:
            return '❓';
      }
   }
   // Thêm function mới
   getMaskedContent = async (originalContent: string): Promise<string> => {
      // Mock function - thực tế sẽ gọi API
      // Trong thực tế, bạn sẽ gửi originalContent đến server để xử lý

      // Giả lập thời gian phản hồi
      await new Promise(resolve => setTimeout(resolve, 200));

      // Tạo nội dung masked theo từng loại nội dung
      if (originalContent.includes('password') || originalContent.includes('mật khẩu')) {
         return 'Nội dung đã được ẩn vì chứa thông tin nhạy cảm liên quan đến mật khẩu';
      }

      if (originalContent.includes('@')) {
         return 'Nội dung đã được ẩn vì chứa thông tin liên hệ cá nhân';
      }

      if (originalContent.length > 50) {
         return 'Nội dung dài đã được ẩn để bảo vệ thông tin';
      }

      // Default mask
      return '[Nội dung đã được ẩn]';
   };
}

export const safetyService = new SafetyService();
