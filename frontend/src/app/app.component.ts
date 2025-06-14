import { Component } from '@angular/core';
import { PaymentFormComponent } from './payment-form/payment-form.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [PaymentFormComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'frontend';
}
