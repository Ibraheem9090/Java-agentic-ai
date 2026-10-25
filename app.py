import streamlit as st
import requests
import json

# Page Configuration
st.set_page_config(
    page_title="AI Jira-to-Code Pipeline",
    page_icon="🤖",
    layout="wide"
)

# App Header
st.title("🚀 AI-Driven Component & Test Generation Pipeline")
st.markdown("Bridge Jira requirements directly to production-ready code and test suites in seconds.")

# Sidebar Configuration
st.sidebar.header("⚙️ Pipeline Settings")
backend_url = st.sidebar.text_input(
    "Spring Boot Backend API URL", 
    value="http://localhost:8080/api/v1/generate"
)
target_stack = st.sidebar.selectbox(
    "Target Stack", 
    ["React 18 + TypeScript (Frontend)", "Java Spring Boot (Backend)"]
)
model_selection = st.sidebar.selectbox(
    "LLM Engine", 
    ["Enterprise LLM (NIM / Custom)", "Local Quantized SLM"]
)

# Main Interface
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 Jira Ticket Details")
    jira_id = st.text_input("Jira Ticket ID", placeholder="e.g., PROJ-4021")
    ticket_title = st.text_input("Ticket Title", placeholder="e.g., User Subscription Status Widget")
    acceptance_criteria = st.text_area(
        "Acceptance Criteria (AC)", 
        height=180,
        placeholder="1. The user subscription badge must reflect active/expired status.\n2. Clicking renewal triggers API integration.\n3. Accessible via keyboard navigation (ARIA roles)."
    )
    
    generate_btn = st.button("Generate Code & Test Suite", type="primary", use_container_width=True)

with col2:
    st.subheader("💻 Generated Output & Preview")
    
    if generate_btn:
        if not ticket_title or not acceptance_criteria:
            st.warning("Please provide both a ticket title and acceptance criteria.")
        else:
            with st.spinner("Analyzing acceptance criteria and generating code..."):
                try:
                    # Payload for backend service
                    payload = {
                        "jiraId": jira_id,
                        "title": ticket_title,
                        "acceptanceCriteria": acceptance_criteria,
                        "stack": target_stack
                    }
                    
                    # Optional: Uncomment if connecting to your Spring Boot backend
                    # response = requests.post(backend_url, json=payload, timeout=30)
                    # result = response.json()
                    
                    # Simulated mock response for demonstration
                    st.success("Pipeline executed successfully!")
                    
                    tab_code, tab_tests, tab_ac = st.tabs(["Generated Code", "Test Suite", "Parsed AC Schema"])
                    
                    with tab_code:
                        if "React" in target_stack:
                            st.code("""
import React, { useState } from 'react';

interface SubscriptionWidgetProps {
  status: 'ACTIVE' | 'EXPIRED';
  onRenew: () => void;
}

export const SubscriptionWidget: React.FC<SubscriptionWidgetProps> = ({ status, onRenew }) => {
  return (
    <div className="p-4 rounded-lg shadow-md bg-white border border-gray-200">
      <span data-testid="sub-status" className={status === 'ACTIVE' ? 'text-green-600' : 'text-red-600'}>
        Status: {status}
      </span>
      {status === 'EXPIRED' && (
        <button onClick={onRenew} className="ml-4 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">
          Renew Now
        </button>
      )}
    </div>
  );
};
                            """, language="typescript")
                        else:
                            st.code("""
@RestController
@RequestMapping("/api/subscriptions")
public class SubscriptionController {
    @GetMapping("/{userId}/status")
    public ResponseEntity<SubscriptionStatusResponse> getStatus(@PathVariable String userId) {
        return ResponseEntity.ok(new SubscriptionStatusResponse(userId, "ACTIVE"));
    }
}
                            """, language="java")
                            
                    with tab_tests:
                        if "React" in target_stack:
                            st.code("""
import { render, screen, fireEvent } from '@testing-library/react';
import { SubscriptionWidget } from './SubscriptionWidget';

describe('SubscriptionWidget AC Validation', () => {
  it('AC1: displays expired status correctly and renders renewal button', () => {
    const handleRenew = vi.fn();
    render(<SubscriptionWidget status="EXPIRED" onRenew={handleRenew} />);
    
    expect(screen.getByTestId('sub-status')).toHaveTextContent('Status: EXPIRED');
    const renewBtn = screen.getByRole('button', { name: /renew now/i });
    fireEvent.click(renewBtn);
    expect(handleRenew).toHaveBeenCalledTimes(1);
  });
});
                            """, language="typescript")
                        else:
                            st.code("""
@SpringBootTest
class UserSubscriptionStatusApplicationTest {
    @Test
    void contextLoads() {
        assertNotNull(SpringApplication.class);
    }
}
                            """, language="java")
                            
                    with tab_ac:
                        st.json({
                            "extractedACs": [
                                {"id": "AC1", "behavior": "Verify status display matches backend state"},
                                {"id": "AC2", "behavior": "Ensure renew action triggers callback on expiration"}
                            ]
                        })

                except requests.exceptions.ConnectionError:
                    st.error(f"Could not connect to backend service at `{backend_url}`. Ensure your Spring Boot service is running.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    else:
        st.info("Fill out the Jira details on the left and click 'Generate Code & Test Suite' to start the pipeline.")

# Footer
st.markdown("---")
st.markdown("Shift-Left Quality Assurance • Powered by Enterprise LLM Orchestration")