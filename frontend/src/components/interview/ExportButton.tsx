import { useState } from 'react';
import { Download, Loader2 } from 'lucide-react';
import { Button } from '../ui/Button';
import { interviewsAPI } from '../../lib/api';
import { useToast } from '../../hooks/useToast';

interface ExportButtonProps {
  interviewId: string;
  className?: string;
}

export function ExportButton({ interviewId, className }: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false);
  const { success, error: showError } = useToast();

  const handleExport = async () => {
    try {
      setIsExporting(true);

      // Fetch PDF blob from API
      const response = await interviewsAPI.exportPDF(interviewId);

      // Create blob from response
      const blob = new Blob([response.data], { type: 'application/pdf' });

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `interview-${interviewId}.pdf`;

      // Trigger download
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      success('PDF exported successfully');
    } catch (error) {
      console.error('Error exporting PDF:', error);
      showError('Failed to export PDF', 'Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Button
      variant="secondary"
      onClick={handleExport}
      disabled={isExporting}
      className={className}
      leftIcon={isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
    >
      {isExporting ? 'Exporting...' : 'Export PDF'}
    </Button>
  );
}
