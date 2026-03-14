/**
 * GasScreen.jsx
 * Services: Pay Bill | New Connection | Safety Complaint
 */
import ServiceLayout      from './ServiceLayout';
import ServiceRequestForm from './ServiceRequestForm';

const TILES = [
  { action: 'pay_bill',   icon: '💳', label: 'Pay Bill',          sub: 'Pay your gas bill'               },
  { action: 'new_conn',   icon: '🔗', label: 'New Connection',    sub: 'Apply for new gas connection'    },
  { action: 'safety',     icon: '🚨', label: 'Safety Complaint',  sub: 'Report gas leak or hazard'       },
];

function NewConnectionForm({ onClose }) {
  return (
    <ServiceRequestForm
      title="New Gas Connection"
      icon="🔗"
      dept="gas"
      endpoint="new-connection"
      onClose={onClose}
      fields={[
        { name: 'full_name',      label: 'Full Name',         type: 'text',     placeholder: 'e.g. Suresh Babu',       required: true  },
        { name: 'address',        label: 'Address',           type: 'textarea', placeholder: 'Full address with pin',  required: true  },
        { name: 'phone',          label: 'Mobile Number',     type: 'tel',      placeholder: '10-digit number',        required: true  },
        { name: 'id_proof',       label: 'ID Proof Type',     type: 'select',   required: true, options: [
            { value: 'aadhaar', label: 'Aadhaar Card' },
            { value: 'pan',     label: 'PAN Card'     },
            { value: 'voter',   label: 'Voter ID'     },
          ]},
        { name: 'id_number',      label: 'ID Number',         type: 'text',     placeholder: 'Document number',       required: true  },
        { name: 'connection_type',label: 'Connection Type',   type: 'select',   required: true, options: [
            { value: 'domestic',   label: 'Domestic'   },
            { value: 'commercial', label: 'Commercial' },
          ]},
      ]}
    />
  );
}

function SafetyComplaintForm({ onClose }) {
  return (
    <ServiceRequestForm
      title="Gas Safety Complaint"
      icon="🚨"
      dept="gas"
      endpoint="safety-complaint"
      onClose={onClose}
      fields={[
        { name: 'consumer_no',  label: 'Consumer Number',   type: 'text',     placeholder: 'e.g. GAS-2204-001',     required: true  },
        { name: 'issue_type',   label: 'Issue Type',        type: 'select',   required: true, options: [
            { value: 'leak',       label: '🔴 Gas Leak — Immediate Danger'    },
            { value: 'smell',      label: '🟡 Unusual Smell — Possible Leak'  },
            { value: 'pressure',   label: '🟡 Low / No Gas Pressure'         },
            { value: 'meter',      label: '🟢 Meter Issue'                    },
            { value: 'other',      label: '🟢 Other Safety Concern'           },
          ]},
        { name: 'location',     label: 'Location / Landmark', type: 'text',   placeholder: 'Where the issue is',    required: true  },
        { name: 'description',  label: 'Description',         type: 'textarea',placeholder: 'Describe the issue',  required: true  },
        { name: 'phone',        label: 'Callback Number',     type: 'tel',    placeholder: '10-digit number',       required: true  },
      ]}
    />
  );
}

const FORM_MODALS = {
  new_conn: NewConnectionForm,
  safety:   SafetyComplaintForm,
};

export default function GasScreen() {
  return (
    <ServiceLayout
      dept="gas"
      icon="🔥"
      gradient="bg-gradient-to-r from-orange-500 to-red-500"
      title="Gas Services"
      tiles={TILES}
      formModals={FORM_MODALS}
    />
  );
}
