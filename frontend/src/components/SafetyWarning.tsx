import { AlertTriangle, Shield, X } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { SafetyResult } from '@/services/safetyService';

interface SafetyWarningProps {
  analysis: SafetyResult;
  onDismiss?: () => void;
  onProceed?: () => void;
  type: 'message' | 'file';
  fileName?: string;
}

export default function SafetyWarning({ 
  analysis, 
  onDismiss, 
  onProceed, 
  type,
  fileName 
}: SafetyWarningProps) {
  if (analysis.isSafe) {
    return null;
  }

  const getAlertVariant = () => {
    switch (analysis.riskLevel) {
      case 'high':
        return 'destructive';
      case 'medium':
        return 'default';
      default:
        return 'default';
    }
  };

  const getTitle = () => {
    switch (analysis.riskLevel) {
      case 'high':
        return `🚨 Cảnh báo ${type === 'file' ? 'file' : 'tin nhắn'} nguy hiểm`;
      case 'medium':
        return `⚠️ Cảnh báo ${type === 'file' ? 'file' : 'tin nhắn'} có rủi ro`;
      default:
        return `ℹ️ Thông báo về ${type === 'file' ? 'file' : 'tin nhắn'}`;
    }
  };

  const getRiskLevelColor = () => {
    switch (analysis.riskLevel) {
      case 'high':
        return 'text-red-600 dark:text-red-400';
      case 'medium':
        return 'text-yellow-600 dark:text-yellow-400';
      default:
        return 'text-blue-600 dark:text-blue-400';
    }
  };

  return (
    <Alert variant={getAlertVariant()} className="mb-4 border-l-4 max-w-4xl mx-4 md:mx-8 lg:mx-auto absolute -top-60 right-1/2 translate-x-1/2 bg-white">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-1">
          {analysis.riskLevel === 'high' ? (
            <AlertTriangle className="h-5 w-5" />
          ) : (
            <Shield className="h-5 w-5" />
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <AlertTitle className="text-sm font-semibold mb-2">
            {getTitle()}
            {fileName && (
              <span className="font-normal text-xs ml-2 opacity-75">
                ({fileName})
              </span>
            )}
          </AlertTitle>
          
          <AlertDescription className="text-sm space-y-2">
            <div>
              <span className="font-medium">Mức độ rủi ro: </span>
              <span className={getRiskLevelColor()}>
                {analysis.riskLevel === 'high' ? 'Cao' : 
                 analysis.riskLevel === 'medium' ? 'Trung bình' : 'Thấp'}
              </span>
            </div>
            
            {analysis.reasons.length > 0 && (
              <div>
                <span className="font-medium">Lý do:</span>
                <ul className="list-disc list-inside ml-4 mt-1 space-y-1">
                  {analysis.reasons.map((reason, index) => (
                    <li key={index} className="text-xs">{reason}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {analysis.suggestions && analysis.suggestions.length > 0 && (
              <div>
                <span className="font-medium">Đề xuất:</span>
                <ul className="list-disc list-inside ml-4 mt-1 space-y-1">
                  {analysis.suggestions.map((suggestion, index) => (
                    <li key={index} className="text-xs text-blue-600 dark:text-blue-400">
                      {suggestion}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </AlertDescription>
        </div>
        
        <div className="flex-shrink-0 flex flex-col gap-2">
          {onDismiss && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onDismiss}
              className="h-6 w-6 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
      
      {(onProceed || onDismiss) && (
        <div className="flex gap-2 mt-3 pt-3 border-t border-border/50">
          {onDismiss && (
            <Button variant="outline" size="sm" onClick={onDismiss}>
              Hủy
            </Button>
          )}
          {onProceed && (
            <Button 
              variant={analysis.riskLevel === 'high' ? 'destructive' : 'default'} 
              size="sm" 
              onClick={onProceed}
            >
              {analysis.riskLevel === 'high' ? 'Tiếp tục dù có rủi ro' : 'Tiếp tục'}
            </Button>
          )}
        </div>
      )}
    </Alert>
  );
}
