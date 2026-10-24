import os
import re
import tempfile
import subprocess
import streamlit as st
from openai import OpenAI

# 1. Page Configuration
st.set_page_config(
    page_title="Jira AI Java & JUnit Generator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling for enterprise look
st.markdown("""
    <style>
    .main { background-color: #0f172a; color: #f1f5f9; }
    .stTextInput input, .stTextArea textarea {
        background-color: #0f172a !important;
        color: #f1f5f9 !important;
        border: 1px solid #475569 !important;
        border-radius: 6px;
    }
    .stButton button {
        background-color: #2563eb !important;
        color: white !important;
        font-weight: bold;
        border-radius: 6px;
        border: none;
    }
    .stButton button:hover {
        background-color: #3b82f6 !important;
    }
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 16px;
        margin-bottom: 24px;
    }
    .success-box { color: #4ade80; background: #064e3b; border: 1px solid #065f46; padding: 12px; border-radius: 6px; font-family: monospace; white-space: pre-wrap; font-size: 13px; }
    .error-box { color: #f87171; background: #450a0a; border: 1px solid #991b1b; padding: 12px; border-radius: 6px; font-family: monospace; white-space: pre-wrap; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# 2. Safe API Key Retrieval (Handles Streamlit Cloud Secrets & Local Env Variables)
api_key = None
try:
    if "NVIDIA_API_KEY" in st.secrets:
        api_key = st.secrets["NVIDIA_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = os.getenv("NVIDIA_API_KEY")

if not api_key:
    st.error("Missing NVIDIA_API_KEY! Please configure it in Streamlit Cloud Secrets or your environment variables.")
    st.stop()

clean_api_key = api_key.replace("Bearer ", "").strip()

# Using stable Llama 3.3 70B model on NVIDIA NIM
MODEL_NAME = "meta/llama-3.2-11b-vision-instruct"

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=clean_api_key
)

def clean_code(raw_text: str) -> str:
    # 1. Try matching fully closed markdown code blocks
    code_block_match = re.search(r'```(?:java|xml)?\s*([\s\S]*?)```', raw_text, re.IGNORECASE)
    if code_block_match:
        return code_block_match.group(1).strip()

    # 2. Fallback for truncated LLM responses (missing closing ```)
    cleaned = re.sub(r'^\s*```(?:java|xml)?\s*', '', raw_text, flags=re.IGNORECASE)
    cleaned = re.sub(r'^\s*(?:java|xml)\n', '', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace('```', '').strip()
    return cleaned

def generate_llm_response(prompt: str, system_prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=4000,
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"// Error communicating with NVIDIA API: {str(e)}"

def run_maven_tests(java_code: str, test_code: str) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. Create standard Maven directory structure
        main_dir = os.path.join(temp_dir, "src/main/java/com/enterprise/service")
        test_dir = os.path.join(temp_dir, "src/test/java/com/enterprise/service")
        os.makedirs(main_dir, exist_ok=True)
        os.makedirs(test_dir, exist_ok=True)

        # 2. Auto-fix any javax.persistence imports to jakarta.persistence for Spring Boot 3 compatibility
        java_code = java_code.replace("javax.persistence", "jakarta.persistence")

        # 3. Dynamically extract public class name
        service_class_match = re.search(r'public\s+(?:class|interface|enum)\s+(\w+)', java_code)
        service_class_name = service_class_match.group(1) if service_class_match else "SubscriptionService"

        test_class_match = re.search(r'public\s+(?:class|interface|enum)\s+(\w+)', test_code)
        test_class_name = test_class_match.group(1) if test_class_match else "SubscriptionServiceTest"

        # 4. Write source and test files
        with open(os.path.join(main_dir, f"{service_class_name}.java"), "w", encoding="utf-8") as f:
            f.write(java_code)
        with open(os.path.join(test_dir, f"{test_class_name}.java"), "w", encoding="utf-8") as f:
            f.write(test_code)

        # 5. Write pom.xml including spring-boot-starter-data-jpa for Jakarta persistence support
        pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.enterprise</groupId>
    <artifactId>jira-ai-service</artifactId>
    <version>1.0-SNAPSHOT</version>
    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
            <version>3.2.0</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
            <version>3.2.0</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
            <version>3.2.0</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <version>3.2.0</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
"""
        with open(os.path.join(temp_dir, "pom.xml"), "w", encoding="utf-8") as f:
            f.write(pom_content)

        # 6. Run Maven test suite execution
        try:
            res = subprocess.run(
                ["mvn", "test", f"-Dtest={test_class_name}"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=90,
                shell=False
            )
            passed = (res.returncode == 0)
            output = res.stdout if passed else res.stdout + "\n" + res.stderr
            return passed, output
        except Exception as e:
            return False, f"Maven Execution Error: {str(e)}"

# 3. Main Dashboard UI Layout
st.markdown("""
    <div class="header-container">
        <h1 style="font-size: 24px; font-weight: bold; color: #60a5fa; margin: 0;">Jira AI Java & JUnit Test Generator</h1>
        <span style="font-size: 14px; font-weight: 600; color: #94a3b8;">Designed & Developed by <span style="color: #93c5fd;">Aafreen Shaikh</span></span>
    </div>
""", unsafe_allow_html=True)

# Input Card Container
with st.container():
    summary_input = st.text_input("Jira Summary", value="User Subscription Status API with Discount Rules")
    desc_input = st.text_area("Jira Description", value="Create a REST endpoint POST /api/v1/subscriptions/calculate that accepts user ID and plan type (BASIC, PREMIUM). If the user has been active for over 2 years, apply a 20% loyalty discount. Throw a custom UserNotFoundException (404) if user does not exist.")
    run_button = st.button("Run Java Pipeline")

# Default Java code for initial page load
DEFAULT_JAVA_CODE = """package com.enterprise.service;

import java.math.BigDecimal;
import org.springframework.stereotype.Service;

@Service
public class SubscriptionService {
    public BigDecimal calculatePrice(String planType, boolean isLoyaltyCustomer) {
        BigDecimal base = planType.equals("PREMIUM") ? new BigDecimal("200.00") : new BigDecimal("100.00");
        return isLoyaltyCustomer ? base.multiply(new BigDecimal("0.80")) : base;
    }
}"""

DEFAULT_TEST_CODE = """package com.enterprise.service;

import org.junit.jupiter.api.Test;
import java.math.BigDecimal;
import static org.junit.jupiter.api.Assertions.assertEquals;

class SubscriptionServiceTest {
    @Test
    void testLoyaltyDiscount() {
        SubscriptionService service = new SubscriptionService();
        BigDecimal price = service.calculatePrice("PREMIUM", true);
        assertEquals(new BigDecimal("160.000"), price);
    }
}"""

# Session state initialization
if "java_code_output" not in st.session_state:
    st.session_state.java_code_output = DEFAULT_JAVA_CODE
if "java_test_output" not in st.session_state:
    st.session_state.java_test_output = DEFAULT_TEST_CODE
if "maven_result" not in st.session_state:
    st.session_state.maven_result = (True, "[INFO] Initial state: Ready for pipeline execution.")

if run_button:
    status_box = st.status("Starting Java pipeline execution...", expanded=True)
    
    try:
        # Stage 1: Java Spring Boot Code Generation
        status_box.update(label="Stage 1: Generating Spring Boot Service & Controller via NVIDIA API...", state="running")
        prompt_java = (
            f"Write complete, production-grade Spring Boot service and controller code for: {summary_input}. "
            f"Description: {desc_input}. "
            f"Include package declaration, DTO records or classes, and proper exception handling. Output ONLY executable Java code in a markdown block."
        )
        raw_java = generate_llm_response(prompt_java, "You are a senior enterprise Java and Spring Boot architect. Always output clean, compilable Java code enclosed in a markdown block.")
        java_code = clean_code(raw_java)
        st.session_state.java_code_output = java_code
        status_box.write("✓ Stage 1 Complete: Spring Boot code generated!")

        # Stage 2: JUnit 5 & Mockito Test Generation
        status_box.update(label="Stage 2: Writing Requirement-Driven JUnit 5 & Mockito Tests...", state="running")
        test_prompt = f"Write comprehensive JUnit 5 and Mockito unit tests directly derived from the acceptance criteria for this Java code:\n\n{java_code}"
        raw_test = generate_llm_response(test_prompt, "You are a senior Java QA engineer. Write robust unit test cases using JUnit 5 and Mockito matching the service specifications. Output ONLY executable code in a markdown block.")
        test_code = clean_code(raw_test)
        st.session_state.java_test_output = test_code
        status_box.write("✓ Stage 2 Complete: JUnit test cases generated!")

        # Stage 3: Maven Test Execution
        status_box.update(label="Stage 3: Compiling and Running Maven Test Suite...", state="running")
        passed, out = run_maven_tests(java_code, test_code)
        st.session_state.maven_result = (passed, out)
        status_box.write(f"✓ Stage 3 Complete (Maven Build & Test Passed: {passed})")

        status_box.update(label="Java Pipeline Execution Complete!", state="complete", expanded=False)
        st.rerun()

    except Exception as e:
        status_box.update(label=f"Pipeline Failed: {str(e)}", state="error")

# 4. Result Dashboard Panes (2-Column Grid Layout)
col1, col2 = st.columns(2)

with col1:
    st.markdown("<h3 style='color: #4ade80; font-size: 14px;'>Spring Boot Source Code (Service & Controller)</h3>", unsafe_allow_html=True)
    st.code(st.session_state.java_code_output, language="java")
    
    st.markdown("<h3 style='color: #facc15; font-size: 14px;'>JUnit 5 & Mockito Test Suite</h3>", unsafe_allow_html=True)
    st.code(st.session_state.java_test_output, language="java")

with col2:
    st.markdown("<h3 style='color: #c084fc; font-size: 14px;'>Maven Test Execution Output</h3>", unsafe_allow_html=True)
    passed, logs = st.session_state.maven_result
    if passed:
        st.markdown(f'<div class="success-box"><b>STATUS: SUCCESS (Build & Tests Passed)</b>\n\n{logs}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="error-box"><b>STATUS: FAILURE (Compilation / Test Error)</b>\n\n{logs}</div>', unsafe_allow_html=True)