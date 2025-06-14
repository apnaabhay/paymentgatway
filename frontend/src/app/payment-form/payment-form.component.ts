import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface PaymentResult {
  status: 'approved' | 'declined' | 'error';
  message: string;
  transaction_id?: string;
}

@Component({
  selector: 'app-payment-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './payment-form.component.html',
  styleUrls: ['./payment-form.component.css']
})
export class PaymentFormComponent {
  result: PaymentResult | null = null;
  cardNumber: string = '';
  expiryDate: string = '';
  cvv: string = '';

  onSubmit() {
    // Simulate payment processing
    this.result = {
      status: 'approved',
      message: 'Payment processed successfully',
      transaction_id: 'TRX' + Math.random().toString(36).substr(2, 9)
    };
  }
} 