/**
 * Reporting service for SoftBankCashWire frontend
 * Handles report generation and export functionality
 */

import { apiService } from './apiService';

export interface ReportPeriod {
  start_date: string;
  end_date: string;
  duration_days: number;
}

export interface TransactionSummaryReport {
  report_type: 'TRANSACTION_SUMMARY';
  period: ReportPeriod;
  user_id?: string;
  summary: {
    total_transactions: number;
    total_volume: string;
    average_transaction_amount: string;
    transfer_count: number;
    event_contribution_count: number;
    average_transfer_amount: string;
    average_contribution_amount: string;
  };
  category_breakdown: Array<{
    category: string;
    transaction_count: number;
    total_amount: string;
    average_amount: string;
    percentage_of_volume: number;
  }>;
  generated_at: string;
}

export interface UserActivityReport {
  report_type: 'USER_ACTIVITY';
  period: ReportPeriod;
  summary: {
    total_users: number;
    active_users: number;
  };
  user_activities: Array<{
    user_id: string;
    user_name: string;
    user_email: string;
    user_role: string;
    current_balance: string;
    transaction_activity: {
      total_transactions: number;
      sent_count: number;
      received_count: number;
      total_sent: string;
      total_received: string;
      net_amount: string;
    };
    request_activity: {
      sent_requests: number;
      received_requests: number;
    };
    event_activity: {
      created_events: number;
      event_contributions: number;
    };
    last_login: string | null;
  }>;
  generated_at: string;
}

export interface EventAccountReport {
  report_type: 'EVENT_ACCOUNT';
  period: ReportPeriod;
  summary: {
    total_events: number;
    active_events: number;
    completed_events: number;
    expired_events: number;
    total_target_amount: string;
    total_raised_amount: string;
    overall_progress_percentage: number;
  };
  events: Array<{
    event_id: string;
    event_name: string;
    event_description: string;
    creator_id: string;
    creator_name: string;
    status: string;
    target_amount: string;
    current_amount: string;
    remaining_amount: string;
    progress_percentage: number;
    contribution_count: number;
    unique_contributors: number;
    average_contribution: string;
    created_at: string;
    deadline: string | null;
    is_expired: boolean;
  }>;
  generated_at: string;
}

export interface PersonalAnalytics {
  report_type: 'PERSONAL_ANALYTICS';
  user_id: string;
  user_name: string;
  period: ReportPeriod;
  summary: {
    total_transactions: number;
    total_sent: string;
    total_received: string;
    net_amount: string;
    current_balance: string;
  };
  spending_analysis: {
    categories: Array<{
      category: string;
      amount: string;
      percentage: number;
    }>;
    monthly_trends: Array<{
      month: string;
      sent: string;
      received: string;
      net: string;
    }>;
  };
  money_requests: {
    sent_count: number;
    received_count: number;
    approved_sent: number;
    approved_received: number;
  };
  event_participation: {
    created_events: number;
    contributions_count: number;
    total_contributed: string;
  };
  generated_at: string;
}

export interface AvailableReport {
  type: string;
  name: string;
  description: string;
  parameters: string[];
}

export interface ReportRequest {
  start_date: string;
  end_date: string;
  user_id?: string;
  export_format?: 'json' | 'csv';
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  errors?: string[];
}

class ReportingService {
  /**
   * Get available reports for current user
   */
  async getAvailableReports(): Promise<AvailableReport[]> {
    try {
      const response = await apiService.get<ApiResponse<{ reports: AvailableReport[] }>>('/reporting/available');
      
      if (response.success && response.data) {
        return response.data.reports;
      }
      
      throw new Error(response.error || 'Failed to get available reports');
    } catch (error) {
      console.error('Error getting available reports:', error);
      throw error;
    }
  }

  /**
   * Generate transaction summary report
   */
  async generateTransactionSummary(request: ReportRequest): Promise<TransactionSummaryReport | Blob> {
    try {
      if (request.export_format === 'csv') {
        // Handle CSV export as blob
        const response = await fetch('/api/reporting/transaction-summary', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...apiService.getAuthHeaders(),
          },
          body: JSON.stringify(request),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to generate report');
        }

        return await response.blob();
      }

      const response = await apiService.post<ApiResponse<TransactionSummaryReport>>('/reporting/transaction-summary', request);
      
      if (response.success && response.data) {
        return response.data;
      }
      
      throw new Error(response.error || response.errors?.join(', ') || 'Failed to generate transaction summary');
    } catch (error) {
      console.error('Error generating transaction summary:', error);
      throw error;
    }
  }

  /**
   * Generate user activity report
   */
  async generateUserActivityReport(request: Omit<ReportRequest, 'user_id'>): Promise<UserActivityReport | Blob> {
    try {
      if (request.export_format === 'csv') {
        // Handle CSV export as blob
        const response = await fetch('/api/reporting/user-activity', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...apiService.getAuthHeaders(),
          },
          body: JSON.stringify(request),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to generate report');
        }

        return await response.blob();
      }

      const response = await apiService.post<ApiResponse<UserActivityReport>>('/reporting/user-activity', request);
      
      if (response.success && response.data) {
        return response.data;
      }
      
      throw new Error(response.error || response.errors?.join(', ') || 'Failed to generate user activity report');
    } catch (error) {
      console.error('Error generating user activity report:', error);
      throw error;
    }
  }

  /**
   * Generate event account report
   */
  async generateEventAccountReport(request: Omit<ReportRequest, 'user_id'>): Promise<EventAccountReport | Blob> {
    try {
      if (request.export_format === 'csv') {
        // Handle CSV export as blob
        const response = await fetch('/api/reporting/event-accounts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...apiService.getAuthHeaders(),
          },
          body: JSON.stringify(request),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to generate report');
        }

        return await response.blob();
      }

      const response = await apiService.post<ApiResponse<EventAccountReport>>('/reporting/event-accounts', request);
      
      if (response.success && response.data) {
        return response.data;
      }
      
      throw new Error(response.error || response.errors?.join(', ') || 'Failed to generate event account report');
    } catch (error) {
      console.error('Error generating event account report:', error);
      throw error;
    }
  }

  /**
   * Generate personal analytics
   */
  async generatePersonalAnalytics(request: ReportRequest): Promise<PersonalAnalytics | Blob> {
    try {
      if (request.export_format === 'csv') {
        // Handle CSV export as blob
        const response = await fetch('/api/reporting/personal-analytics', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...apiService.getAuthHeaders(),
          },
          body: JSON.stringify(request),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to generate report');
        }

        return await response.blob();
      }

      const response = await apiService.post<ApiResponse<PersonalAnalytics>>('/reporting/personal-analytics', request);
      
      if (response.success && response.data) {
        return response.data;
      }
      
      throw new Error(response.error || response.errors?.join(', ') || 'Failed to generate personal analytics');
    } catch (error) {
      console.error('Error generating personal analytics:', error);
      throw error;
    }
  }

  /**
   * Download exported report file
   */
  downloadFile(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  /**
   * Format currency amount for display
   */
  formatCurrency(amount: string): string {
    const num = parseFloat(amount);
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
    }).format(num);
  }

  /**
   * Format percentage for display
   */
  formatPercentage(percentage: number): string {
    return `${percentage.toFixed(2)}%`;
  }

  /**
   * Format date for display
   */
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  }

  /**
   * Format datetime for display
   */
  formatDateTime(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleString('en-GB', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  /**
   * Get default date range (last 30 days)
   */
  getDefaultDateRange(): { start_date: string; end_date: string } {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);

    return {
      start_date: startDate.toISOString(),
      end_date: endDate.toISOString(),
    };
  }

  /**
   * Validate date range
   */
  validateDateRange(startDate: string, endDate: string): string[] {
    const errors: string[] = [];
    const start = new Date(startDate);
    const end = new Date(endDate);

    if (isNaN(start.getTime())) {
      errors.push('Invalid start date');
    }

    if (isNaN(end.getTime())) {
      errors.push('Invalid end date');
    }

    if (start >= end) {
      errors.push('Start date must be before end date');
    }

    const daysDiff = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
    if (daysDiff > 730) {
      errors.push('Date range cannot exceed 2 years');
    }

    return errors;
  }
}

export const reportingService = new ReportingService();