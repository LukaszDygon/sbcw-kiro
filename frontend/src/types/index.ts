/**
 * TypeScript type definitions for SoftBankCashWire
 */

export enum UserRole {
  EMPLOYEE = 'EMPLOYEE',
  ADMIN = 'ADMIN',
  FINANCE = 'FINANCE'
}

export enum AccountStatus {
  ACTIVE = 'ACTIVE',
  SUSPENDED = 'SUSPENDED',
  CLOSED = 'CLOSED'
}

export enum TransactionType {
  TRANSFER = 'TRANSFER',
  EVENT_CONTRIBUTION = 'EVENT_CONTRIBUTION'
}

export enum TransactionStatus {
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED'
}

export enum EventStatus {
  ACTIVE = 'ACTIVE',
  CLOSED = 'CLOSED',
  CANCELLED = 'CANCELLED'
}

export enum RequestStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  DECLINED = 'DECLINED',
  EXPIRED = 'EXPIRED'
}

export interface User {
  id: string
  microsoft_id?: string
  email: string
  name: string
  role: UserRole | string
  account_status: AccountStatus | string
  created_at: string
  last_login: string
  permissions?: string[]
}

export interface Account {
  id: string
  user_id: string
  balance: string
  currency: string
  created_at: string
  updated_at: string
}

export interface Transaction {
  id: string
  sender_id: string
  recipient_id: string
  amount: string
  transaction_type: TransactionType
  category?: string
  note?: string
  status: TransactionStatus
  created_at: string
  processed_at: string
  sender_name?: string
  recipient_name?: string
}

export interface EventAccount {
  id: string
  creator_id: string
  name: string
  description: string
  target_amount?: string
  deadline?: string
  status: EventStatus
  total_contributions: string
  created_at: string
  closed_at?: string
  creator_name?: string
}

export interface MoneyRequest {
  id: string
  requester_id: string
  recipient_id: string
  amount: string
  note?: string
  status: RequestStatus
  created_at: string
  responded_at?: string
  expires_at: string
  requester_name?: string
  recipient_name?: string
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
}

export enum NotificationType {
  TRANSACTION_RECEIVED = 'TRANSACTION_RECEIVED',
  TRANSACTION_SENT = 'TRANSACTION_SENT',
  MONEY_REQUEST_RECEIVED = 'MONEY_REQUEST_RECEIVED',
  MONEY_REQUEST_APPROVED = 'MONEY_REQUEST_APPROVED',
  MONEY_REQUEST_DECLINED = 'MONEY_REQUEST_DECLINED',
  EVENT_CONTRIBUTION = 'EVENT_CONTRIBUTION',
  EVENT_DEADLINE_APPROACHING = 'EVENT_DEADLINE_APPROACHING',
  EVENT_CLOSED = 'EVENT_CLOSED',
  SYSTEM_MAINTENANCE = 'SYSTEM_MAINTENANCE',
  SECURITY_ALERT = 'SECURITY_ALERT'
}

export enum NotificationPriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  URGENT = 'URGENT'
}

export interface Notification {
  id: string
  user_id: string
  type: NotificationType
  title: string
  message: string
  priority: NotificationPriority
  read: boolean
  data?: Record<string, any>
  created_at: string
  expires_at?: string
}