import { AlertTriangle, Shield, X } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

interface SafetyWarningProps {
  alertContent: string;
  onDismiss?: () => void;
  onProceed?: () => void;
  type: 'message' | 'file';
  fileName?: string;
}

export default function SafetyWarning({
  alertContent,
  onDismiss,
  onProceed,
  type,
  fileName
}: SafetyWarningProps) {
  if (!alertContent) {
    return null;
  }

  const getTitle = () => {
    return "Cảnh báo"
  };


  return (
    <Alert variant={"destructive"} className="mb-4 border-l-4 max-w-4xl mx-4 md:mx-8 lg:mx-auto absolute -top-28 right-1/2 translate-x-1/2 bg-white">
      <div className="flex items-start gap-3">

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

            {alertContent && (
              <div>
                <p className="mt-1">{alertContent}</p>
              </div>
            )}
          </AlertDescription>
        </div>

      </div>
    </Alert>
  );
}
