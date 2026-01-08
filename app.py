import streamlit as st
import time
import os
from datetime import datetime
import logging

# Import RAG Service
from rag_service import RAGService
from config import (
    MODELARTS_ENDPOINT, DEEPSEEK_API_KEY,
    DEEPSEEK_USE_DIRECT_API, LOG_LEVEL
)

# Configure logging for cloud
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==================== HUAWEI THEME CSS ====================
HUAWEI_CSS = """
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Root Variables - Huawei Theme - Enhanced Visibility */
    :root {
        --huawei-red: #C7000B;
        --huawei-red-dark: #9A0008;
        --huawei-red-light: #FF4757;
        --huawei-gradient: linear-gradient(135deg, #C7000B 0%, #FF1744 50%, #C7000B 100%);
        --bg-dark: #0D0D0D;
        --bg-card: #1A1A1A;
        --bg-card-hover: #242424;
        --text-primary: #FFFFFF;
        --text-secondary: #D0D0D0;
        --text-muted: #8A8A8A;
        --border-color: #3D3D3D;
        --success: #00E676;
        --warning: #FFEA00;
        --info: #40C4FF;
    }
    
    /* Global Styles */
    html, body, .stApp, [data-testid="stAppViewContainer"], 
    [data-testid="stHeader"], .main, [data-testid="stMainBlockContainer"],
    [data-testid="stVerticalBlock"], [data-testid="stBottom"] {
        background: #0D0D0D !important;
        background-color: #0D0D0D !important;
    }
    
    .stApp {
        background: #0D0D0D !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* ALL TEXT VISIBILITY FIX */
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label,
    .stMarkdown, .stMarkdown p, .stMarkdown span,
    [data-testid="stMarkdownContainer"], 
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stText"] {
        color: #FFFFFF !important;
    }
    
    /* Expander text fix */
    .streamlit-expanderHeader, 
    .streamlit-expanderHeader p,
    .streamlit-expanderHeader span,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] summary p {
        color: #FFFFFF !important;
    }
    
    .streamlit-expanderContent,
    .streamlit-expanderContent p,
    .streamlit-expanderContent span,
    .streamlit-expanderContent div {
        color: #E0E0E0 !important;
    }
    
    /* Metric text fix */
    [data-testid="stMetricValue"],
    [data-testid="stMetricLabel"],
    .stMetric label,
    .stMetric [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #B0B0B0 !important;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Bottom container - beyaz alanı kaldır */
    [data-testid="stBottom"], 
    [data-testid="stBottomBlockContainer"],
    .stBottom {
        background: transparent !important;
        background-color: transparent !important;
    }
    
    /* Main Container - RESPONSIVE */
    .main .block-container {
        padding: 2rem 1rem;
        max-width: 1200px;
        background: transparent !important;
    }
    
    @media (min-width: 768px) {
        .main .block-container {
            padding: 2rem 2rem;
        }
    }
    
    @media (min-width: 1024px) {
        .main .block-container {
            padding: 2rem 3rem;
        }
    }
    
    .main {
        background: #0D0D0D !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D0D0D 0%, #1A1A1A 100%);
        border-right: 1px solid var(--border-color);
    }
    
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: #E0E0E0 !important;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        background: transparent;
        border: 1px solid var(--border-color);
        color: #E0E0E0 !important;
        padding: 0.75rem 1rem;
        border-radius: 12px;
        font-weight: 500;
        transition: all 0.3s ease;
        margin-bottom: 0.5rem;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: var(--huawei-red);
        border-color: var(--huawei-red);
        color: white !important;
        transform: translateX(5px);
    }
    
    /* Custom Header - RESPONSIVE */
    .huawei-header {
        background: var(--huawei-gradient);
        padding: 1.5rem 1rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 10px 40px rgba(199, 0, 11, 0.3);
    }
    
    @media (min-width: 768px) {
        .huawei-header {
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
        }
    }
    
    .huawei-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .huawei-header h1 {
        color: white !important;
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0;
        position: relative;
        z-index: 1;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    
    @media (min-width: 768px) {
        .huawei-header h1 {
            font-size: 2.5rem;
        }
    }
    
    .huawei-header p {
        color: rgba(255,255,255,0.95) !important;
        font-size: 0.95rem;
        margin-top: 0.5rem;
        position: relative;
        z-index: 1;
    }
    
    @media (min-width: 768px) {
        .huawei-header p {
            font-size: 1.1rem;
        }
    }
    
    /* Feature Cards - RESPONSIVE */
    .feature-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        min-height: auto;
    }
    
    @media (min-width: 768px) {
        .feature-card {
            padding: 1.5rem;
            border-radius: 16px;
            min-height: 180px;
        }
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        border-color: var(--huawei-red);
        box-shadow: 0 10px 30px rgba(199, 0, 11, 0.2);
    }
    
    .feature-icon {
        font-size: 1.75rem;
        margin-bottom: 0.5rem;
    }
    
    @media (min-width: 768px) {
        .feature-icon {
            font-size: 2rem;
        }
    }
    
    .feature-title {
        color: #FFFFFF !important;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    @media (min-width: 768px) {
        .feature-title {
            font-size: 1.1rem;
        }
    }
    
    .feature-desc {
        color: #D0D0D0 !important;
        font-size: 0.85rem;
        line-height: 1.6;
    }
    
    @media (min-width: 768px) {
        .feature-desc {
            font-size: 0.9rem;
        }
    }
    
    /* Architecture Diagram - RESPONSIVE */
    .arch-container {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1.25rem;
        margin: 1.5rem 0;
    }
    
    @media (min-width: 768px) {
        .arch-container {
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
        }
    }
    
    .arch-layer {
        background: linear-gradient(90deg, var(--bg-card-hover) 0%, var(--bg-card) 100%);
        border: 1px solid var(--border-color);
        border-left: 4px solid var(--huawei-red);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    @media (min-width: 768px) {
        .arch-layer {
            border-radius: 12px;
            padding: 1rem 1.5rem;
            margin: 0.75rem 0;
        }
    }
    
    .arch-layer:hover {
        transform: translateX(10px);
        border-left-color: var(--huawei-red-light);
    }
    
    .arch-layer-title {
        color: #FF6B7A !important;
        font-weight: 600;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    @media (min-width: 768px) {
        .arch-layer-title {
            font-size: 0.9rem;
        }
    }
    
    .arch-layer-content {
        color: #FFFFFF !important;
        font-size: 0.9rem;
        margin-top: 0.25rem;
    }
    
    @media (min-width: 768px) {
        .arch-layer-content {
            font-size: 1rem;
        }
    }
    
    /* Chat Messages - ENHANCED VISIBILITY */
    .stChatMessage {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 0.85rem !important;
        margin-bottom: 0.85rem !important;
    }
    
    @media (min-width: 768px) {
        .stChatMessage {
            border-radius: 16px !important;
            padding: 1rem !important;
            margin-bottom: 1rem !important;
        }
    }
    
    [data-testid="stChatMessageContent"],
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] span,
    [data-testid="stChatMessageContent"] div {
        color: #FFFFFF !important;
    }
    
    /* Chat Input - Premium Design - RESPONSIVE */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] * {
        background-color: transparent !important;
    }
    
    [data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
        padding: 1rem !important;
        background: linear-gradient(to top, #0D0D0D 0%, #0D0D0D 80%, transparent 100%) !important;
        z-index: 999 !important;
        margin-left: 0 !important;
        transform: none !important;
    }
    
    @media (min-width: 576px) {
        [data-testid="stChatInput"] {
            padding: 1.25rem 2rem 1.5rem 2rem !important;
        }
    }
    
    @media (min-width: 768px) {
        [data-testid="stChatInput"] {
            padding: 1.5rem calc(50% - 350px + 8rem) 2rem calc(50% - 350px) !important;
        }
    }
    
    @media (min-width: 1024px) {
        [data-testid="stChatInput"] {
            padding: 1.5rem calc(50% - 400px + 10rem) 2rem calc(50% - 400px) !important;
        }
    }
    
    [data-testid="stChatInput"] > div {
        background: linear-gradient(135deg, #1A1A1A 0%, #242424 100%) !important;
        border: 2px solid #4D4D4D !important;
        border-radius: 20px !important;
        padding: 0.25rem 0.4rem !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 
                    0 0 0 1px rgba(255, 255, 255, 0.05) inset !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        max-width: 100% !important;
        margin: 0 auto !important;
    }
    
    @media (min-width: 768px) {
        [data-testid="stChatInput"] > div {
            border-radius: 28px !important;
            padding: 0.35rem 0.5rem !important;
            max-width: 800px !important;
        }
    }
    
    [data-testid="stChatInput"] > div:hover {
        border-color: #606060 !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6),
                    0 0 0 1px rgba(255, 255, 255, 0.08) inset !important;
    }
    
    [data-testid="stChatInput"] > div:focus-within {
        border-color: #C7000B !important;
        box-shadow: 0 12px 40px rgba(199, 0, 11, 0.3),
                    0 0 40px rgba(199, 0, 11, 0.2),
                    0 0 0 1px rgba(199, 0, 11, 0.4) inset !important;
    }
    
    /* Input içi - tüm beyaz alanları kaldır */
    [data-testid="stChatInput"] form,
    [data-testid="stChatInput"] [data-testid="stChatInputContainer"],
    [data-testid="stChatInput"] .stChatInputContainer {
        background: transparent !important;
        border: none !important;
    }
    
    [data-testid="stChatInput"] textarea {
        color: #FFFFFF !important;
        font-size: 0.95rem !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.75rem 1rem !important;
        background: transparent !important;
        line-height: 1.5 !important;
        border: none !important;
        caret-color: #C7000B !important;
    }
    
    @media (min-width: 768px) {
        [data-testid="stChatInput"] textarea {
            font-size: 1rem !important;
            padding: 0.85rem 1.25rem !important;
        }
    }
    
    [data-testid="stChatInput"] textarea::placeholder {
        color: #888888 !important;
        font-style: normal !important;
        opacity: 1 !important;
    }
    
    /* Send Button - RESPONSIVE */
    [data-testid="stChatInput"] button[kind="primary"],
    [data-testid="stChatInput"] button[data-testid="stChatInputSubmitButton"],
    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #C7000B 0%, #E81123 50%, #FF1744 100%) !important;
        border: none !important;
        border-radius: 16px !important;
        min-width: 42px !important;
        width: 42px !important;
        height: 42px !important;
        margin: 0.15rem 0.2rem !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 20px rgba(199, 0, 11, 0.5) !important;
        cursor: pointer !important;
    }
    
    @media (min-width: 768px) {
        [data-testid="stChatInput"] button[kind="primary"],
        [data-testid="stChatInput"] button[data-testid="stChatInputSubmitButton"],
        [data-testid="stChatInput"] button {
            border-radius: 20px !important;
            min-width: 48px !important;
            width: 48px !important;
            height: 48px !important;
            margin: 0.15rem 0.25rem !important;
        }
    }
    
    [data-testid="stChatInput"] button:hover {
        transform: scale(1.1) translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(199, 0, 11, 0.7) !important;
        background: linear-gradient(135deg, #E81123 0%, #FF1744 100%) !important;
    }
    
    [data-testid="stChatInput"] button:active {
        transform: scale(0.95) !important;
        box-shadow: 0 2px 10px rgba(199, 0, 11, 0.5) !important;
    }
    
    [data-testid="stChatInput"] button svg {
        fill: white !important;
        width: 20px !important;
        height: 20px !important;
    }
    
    @media (min-width: 768px) {
        [data-testid="stChatInput"] button svg {
            width: 22px !important;
            height: 22px !important;
        }
    }
    
    /* Bottom bar gradient overlay için */
    [data-testid="stBottomBlockContainer"] {
        background: transparent !important;
    }
    
    /* Streamlit'in varsayılan bottom bar stilini kaldır */
    .stChatFloatingInputContainer {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Add padding at bottom for fixed input - RESPONSIVE */
    .main .block-container {
        padding-bottom: 100px !important;
    }
    
    @media (min-width: 768px) {
        .main .block-container {
            padding-bottom: 140px !important;
        }
    }
    
    /* Expander Styling - ENHANCED VISIBILITY */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: #FFFFFF !important;
    }
    
    .streamlit-expanderContent {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        color: #E0E0E0 !important;
    }
    
    /* Status Indicators - ENHANCED VISIBILITY */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.3rem 0.85rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    @media (min-width: 768px) {
        .status-badge {
            font-size: 0.8rem;
            padding: 0.25rem 0.75rem;
        }
    }
    
    .status-success {
        background: rgba(0, 230, 118, 0.2);
        color: #00E676 !important;
        border: 1px solid #00E676;
    }
    
    .status-info {
        background: rgba(64, 196, 255, 0.2);
        color: #40C4FF !important;
        border: 1px solid #40C4FF;
    }
    
    .status-warning {
        background: rgba(255, 234, 0, 0.2);
        color: #FFEA00 !important;
        border: 1px solid #FFEA00;
    }
    
    /* Metric Cards - RESPONSIVE */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 0.85rem;
        text-align: center;
    }
    
    @media (min-width: 768px) {
        .metric-card {
            border-radius: 12px;
            padding: 1rem;
        }
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #FF6B7A !important;
    }
    
    @media (min-width: 768px) {
        .metric-value {
            font-size: 2rem;
        }
    }
    
    .metric-label {
        color: #D0D0D0 !important;
        font-size: 0.8rem;
        margin-top: 0.25rem;
    }
    
    @media (min-width: 768px) {
        .metric-label {
            font-size: 0.85rem;
        }
    }
    
    /* Warning Box - ENHANCED VISIBILITY */
    .warning-box {
        background: linear-gradient(135deg, rgba(199, 0, 11, 0.15) 0%, rgba(255, 23, 68, 0.1) 100%);
        border: 1px solid rgba(199, 0, 11, 0.4);
        border-radius: 12px;
        padding: 1rem;
        margin: 1.25rem 0;
    }
    
    @media (min-width: 768px) {
        .warning-box {
            padding: 1.25rem;
            margin: 1.5rem 0;
        }
    }
    
    .warning-box p {
        color: #E0E0E0 !important;
        margin: 0;
        line-height: 1.6;
        font-size: 0.9rem;
    }
    
    @media (min-width: 768px) {
        .warning-box p {
            font-size: 1rem;
        }
    }
    
    /* Footer - RESPONSIVE */
    .huawei-footer {
        text-align: center;
        padding: 1.5rem 1rem;
        margin-top: 2rem;
        border-top: 1px solid var(--border-color);
    }
    
    @media (min-width: 768px) {
        .huawei-footer {
            padding: 2rem;
            margin-top: 3rem;
        }
    }
    
    .huawei-footer img {
        height: 30px;
        opacity: 0.8;
    }
    
    .huawei-footer p {
        color: #8A8A8A !important;
        font-size: 0.8rem;
        margin-top: 0.85rem;
    }
    
    @media (min-width: 768px) {
        .huawei-footer p {
            font-size: 0.85rem;
            margin-top: 1rem;
        }
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fade-in {
        animation: fadeIn 0.6s ease forwards;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .animate-pulse {
        animation: pulse 2s infinite;
    }
    
    /* Pipeline Visualization - RESPONSIVE */
    .pipeline-step {
        display: flex;
        align-items: center;
        padding: 0.6rem 0.85rem;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        margin: 0.4rem 0;
    }
    
    @media (min-width: 768px) {
        .pipeline-step {
            padding: 0.75rem 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
    }
    
    .pipeline-step-number {
        width: 24px;
        height: 24px;
        background: var(--huawei-red);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white !important;
        font-weight: 600;
        font-size: 0.75rem;
        margin-right: 0.75rem;
        flex-shrink: 0;
    }
    
    @media (min-width: 768px) {
        .pipeline-step-number {
            width: 28px;
            height: 28px;
            font-size: 0.85rem;
            margin-right: 1rem;
        }
    }
    
    .pipeline-step-text {
        color: #FFFFFF !important;
        font-size: 0.85rem;
    }
    
    @media (min-width: 768px) {
        .pipeline-step-text {
            font-size: 0.95rem;
        }
    }
    
    .pipeline-connector {
        width: 2px;
        height: 16px;
        background: var(--huawei-red);
        margin-left: 11px;
    }
    
    @media (min-width: 768px) {
        .pipeline-connector {
            height: 20px;
            margin-left: 13px;
        }
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-dark);
    }
    
    ::-webkit-scrollbar-thumb {
        background: #4D4D4D;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--huawei-red);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: var(--huawei-red) !important;
    }
    
    /* Buttons - ENHANCED VISIBILITY */
    .stButton > button {
        color: #FFFFFF !important;
    }
    
    .stButton > button[kind="primary"] {
        background: var(--huawei-gradient) !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    
    /* Column layouts - RESPONSIVE */
    [data-testid="column"] {
        padding: 0 0.5rem !important;
    }
    
    @media (max-width: 767px) {
        [data-testid="column"] {
            padding: 0 0.25rem !important;
        }
    }
    
    /* Make columns stack on mobile */
    @media (max-width: 640px) {
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap;
        }
        
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            flex: 1 1 100% !important;
            max-width: 100% !important;
            margin-bottom: 0.5rem;
        }
    }
    
    /* Source box styling - ENHANCED */
    .source-box {
        background: #1A1A1A;
        border-left: 3px solid #C7000B;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border-radius: 0 8px 8px 0;
    }
    
    .source-box strong {
        color: #FF6B7A !important;
    }
    
    .source-box p {
        color: #D0D0D0 !important;
        font-size: 0.85rem;
        margin: 0.5rem 0 0 0;
        white-space: pre-wrap;
    }
</style>
"""

# ==================== HTML COMPONENTS ====================
def render_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div class="huawei-header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def render_feature_card(icon: str, title: str, description: str):
    return f"""
    <div class="feature-card">
        <div class="feature-icon">{icon}</div>
        <div class="feature-title">{title}</div>
        <div class="feature-desc">{description}</div>
    </div>
    """

def render_architecture_layer(title: str, content: str):
    return f"""
    <div class="arch-layer">
        <div class="arch-layer-title">{title}</div>
        <div class="arch-layer-content">{content}</div>
    </div>
    """

def render_metric_card(value: str, label: str):
    return f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """

def render_pipeline_step(number: int, text: str, show_connector: bool = True):
    connector = '<div class="pipeline-connector"></div>' if show_connector else ''
    return f"""
    <div class="pipeline-step">
        <div class="pipeline-step-number">{number}</div>
        <div class="pipeline-step-text">{text}</div>
    </div>
    {connector}
    """

def render_status_badge(text: str, status: str = "info"):
    return f'<span class="status-badge status-{status}">{text}</span>'

def render_warning_box(content: str):
    return f"""
    <div class="warning-box">
        <p>⚠️ <strong>Important Notice:</strong> {content}</p>
    </div>
    """

def render_footer():
    return """
    <div class="huawei-footer">
        <p style="color: #D0D0D0 !important;">🏆 Powered by <strong style="color: #FF6B7A;">Huawei Cloud</strong> Infrastructure</p>
        <p style="font-size: 0.75rem; margin-top: 0.5rem; color: #A0A0A0 !important;">
            ModelArts • Milvus • OBS • ECS • Ascend AI
        </p>
        <p style="font-size: 0.7rem; margin-top: 1rem; color: #707070 !important;">
            © 2024 Spark Infinity Team | Huawei ICT Competition
        </p>
    </div>
    """

# ==================== INITIALIZE RAG SERVICE ====================
@st.cache_resource
def get_rag_service():
    """Initialize and cache RAG service."""
    try:
        return RAGService()
    except Exception as e:
        st.error(f"Error initializing RAG service: {str(e)}")
        return None

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="AI Health Assistant | Huawei Cloud",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown(HUAWEI_CSS, unsafe_allow_html=True)

# Initialize RAG Service
rag_service = get_rag_service()

if not rag_service:
    logger.error("Failed to initialize RAG service")
    st.error("⚠️ Failed to initialize RAG service. Please check your configuration.")
    st.stop()

# Check if LLM is configured (DeepSeek via direct API or ModelArts)
has_deepseek_direct = bool(DEEPSEEK_API_KEY and DEEPSEEK_USE_DIRECT_API)
has_deepseek_modelarts = bool(DEEPSEEK_API_KEY and MODELARTS_ENDPOINT and not DEEPSEEK_USE_DIRECT_API)

if not (has_deepseek_direct or has_deepseek_modelarts):
    logger.error("No LLM configured")
    st.error("⚠️ No LLM configured! Please configure DEEPSEEK_API_KEY in .env file.")
    st.stop()

# ==================== MAIN FUNCTIONS ====================
def generate_medical_response(complaint):
    """Generate medical response using RAG service."""
    if not rag_service:
        return {
            "response": "[Error] RAG service not available.",
            "sources": [],
            "context": "",
            "metadata": {}
        }
    return rag_service.process_query(complaint)

# ==================== SESSION STATE ====================
if "page" not in st.session_state:
    st.session_state.page = "Welcome"
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}
if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {}
if "chat_last_index" not in st.session_state:
    st.session_state.chat_last_index = {}
if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "default_chat_id" not in st.session_state:
    st.session_state.default_chat_id = None

# Create default chat if none exists
if not st.session_state.chat_sessions:
    default_id = datetime.now().strftime("%Y%m%d%H%M%S")
    st.session_state.chat_sessions[default_id] = []
    st.session_state.chat_titles[default_id] = "New Consultation"
    st.session_state.chat_last_index[default_id] = 0
    st.session_state.active_chat = default_id
    st.session_state.default_chat_id = default_id

# ==================== SIDEBAR ====================
with st.sidebar:
    # Logo and Title
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 2rem 0;">
        <h2 style="color: #FF4757; margin: 0; font-weight: 700;">🏥 Health AI</h2>
        <p style="color: #909090; font-size: 0.8rem; margin-top: 0.25rem;">Powered by Huawei Cloud</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation
    st.markdown('<p style="color: #D0D0D0; font-size: 0.85rem; font-weight: 600; margin-bottom: 1rem;">📍 NAVIGATION</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏠", key="nav_home", help="Home"):
            st.session_state.page = "Welcome"
    with col2:
        if st.button("💬", key="nav_chat", help="Chat"):
            st.session_state.page = "Chat"
    with col3:
        if st.button("❓", key="nav_help", help="Help"):
            st.session_state.page = "Help"
    
    st.markdown("---")
    
    # Chat Section (only show on Chat page)
    if st.session_state.page == "Chat":
        st.markdown('<p style="color: #D0D0D0; font-size: 0.85rem; font-weight: 600; margin-bottom: 1rem;">💬 CONSULTATIONS</p>', unsafe_allow_html=True)
        
        if st.button("➕ New Consultation", key="new_chat", use_container_width=True):
            new_id = datetime.now().strftime("%Y%m%d%H%M%S")
            st.session_state.chat_sessions[new_id] = []
            st.session_state.chat_titles[new_id] = "New Consultation"
            st.session_state.chat_last_index[new_id] = 0
            st.session_state.active_chat = new_id
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Chat history
        for chat_id in list(st.session_state.chat_sessions.keys()):
            cols = st.columns([5, 1])
            with cols[0]:
                chat_title = st.session_state.chat_titles.get(chat_id, "Consultation")
                is_active = chat_id == st.session_state.active_chat
                btn_type = "primary" if is_active else "secondary"
                if st.button(f"{'🔵 ' if is_active else '⚪ '}{chat_title[:20]}", key=f"select_{chat_id}", use_container_width=True):
                    st.session_state.active_chat = chat_id
                    st.rerun()
            with cols[1]:
                if st.button("🗑️", key=f"delete_{chat_id}"):
                    st.session_state.chat_sessions.pop(chat_id, None)
                    st.session_state.chat_titles.pop(chat_id, None)
                    st.session_state.chat_last_index.pop(chat_id, None)
                    if st.session_state.active_chat == chat_id:
                        remaining = list(st.session_state.chat_sessions.keys())
                        st.session_state.active_chat = remaining[0] if remaining else None
                    st.rerun()
    
    # System Status
    st.markdown("---")
    st.markdown('<p style="color: #D0D0D0; font-size: 0.85rem; font-weight: 600; margin-bottom: 1rem;">⚡ SYSTEM STATUS</p>', unsafe_allow_html=True)
    
    status_html = f"""
    <div style="font-size: 0.8rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="color: #A0A0A0;">RAG Engine</span>
            <span style="color: #00E676; font-weight: 500;">● Online</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="color: #A0A0A0;">Milvus DB</span>
            <span style="color: #00E676; font-weight: 500;">● Connected</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="color: #A0A0A0;">LLM Service</span>
            <span style="color: #00E676; font-weight: 500;">● Active</span>
        </div>
    </div>
    """
    st.markdown(status_html, unsafe_allow_html=True)

# ==================== MAIN CONTENT ====================
page = st.session_state.page

# --- WELCOME PAGE ---
if page == "Welcome":
    render_header("🏥 AI Health Assistant", "Intelligent Medical Diagnostic Support System")
    
    # Introduction
    st.markdown("""
    <div style="text-align: center; max-width: 800px; margin: 0 auto 2rem auto; padding: 0 1rem;">
        <p style="color: #D0D0D0; font-size: 1rem; line-height: 1.8;">
            Welcome to the AI-powered Health Assistant, built on <strong style="color: #FF4757;">Huawei Cloud</strong> infrastructure.
            This system combines advanced RAG technology with medical knowledge to assist healthcare professionals
            in diagnostic decision-making.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature Cards
    st.markdown("### 🚀 Key Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(render_feature_card(
            "🧠",
            "GraphRAG Technology",
            "Advanced knowledge retrieval combining vector search with graph traversal for comprehensive medical context."
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(render_feature_card(
            "🤖",
            "Agentic RAG",
            "Intelligent task planning and multi-step reasoning for complex medical queries."
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(render_feature_card(
            "☁️",
            "Huawei Cloud Native",
            "Powered by ModelArts, Milvus, and Ascend AI chips for enterprise-grade performance."
        ), unsafe_allow_html=True)
    
    # Architecture Diagram
    st.markdown("### 🏗️ System Architecture")
    
    st.markdown("""
    <div class="arch-container">
        <h4 style="color: #FFFFFF; margin-bottom: 1.5rem; text-align: center;">Cloud-Native RAG Pipeline</h4>
    """, unsafe_allow_html=True)
    
    st.markdown(render_architecture_layer("🔷 Input Layer", "Speech-to-Text Processing • Text Preprocessing • Medical Entity Extraction"), unsafe_allow_html=True)
    st.markdown(render_architecture_layer("🔷 Orchestration Layer", "Agentic Task Planner • Multi-Step Reasoning • Execution Coordinator"), unsafe_allow_html=True)
    st.markdown(render_architecture_layer("🔷 Context Layer", "Milvus Vector Search • GraphRAG Traversal • Context Integration"), unsafe_allow_html=True)
    st.markdown(render_architecture_layer("🔷 Intelligence Layer", "DeepSeek / Qwen LLM • Huawei ModelArts • Ascend AI Acceleration"), unsafe_allow_html=True)
    st.markdown(render_architecture_layer("🔷 Data Layer", "Milvus Cloud • OBS Storage • Medical Knowledge Base"), unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Warning Box
    st.markdown(render_warning_box(
        "This AI-powered health assistant is designed solely for informational purposes and to support the diagnostic process. "
        "The ultimate responsibility for clinical decision-making lies with the physician. System responses cannot replace "
        "professional medical evaluation."
    ), unsafe_allow_html=True)
    
    # CTA Button
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Consultation", key="start_chat", use_container_width=True, type="primary"):
            st.session_state.page = "Chat"
            st.rerun()
    
    # Footer
    st.markdown(render_footer(), unsafe_allow_html=True)

# --- CHAT PAGE ---
elif page == "Chat":
    render_header("💬 Medical Consultation", "AI-Powered Diagnostic Assistant")
    
    # Active chat data
    active = st.session_state.active_chat
    if not active or active not in st.session_state.chat_sessions:
        # Create new chat if none exists
        new_id = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.chat_sessions[new_id] = []
        st.session_state.chat_titles[new_id] = "New Consultation"
        st.session_state.chat_last_index[new_id] = 0
        st.session_state.active_chat = new_id
        active = new_id
    
    history = st.session_state.chat_sessions.get(active, [])
    last_index = st.session_state.chat_last_index.get(active, 0)

    # Pipeline Info (collapsible)
    with st.expander("📊 View RAG Pipeline", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Processing Steps")
            pipeline_html = ""
            pipeline_html += render_pipeline_step(1, "Input Processing & Entity Extraction")
            pipeline_html += render_pipeline_step(2, "Query Embedding Generation")
            pipeline_html += render_pipeline_step(3, "GraphRAG Context Retrieval")
            pipeline_html += render_pipeline_step(4, "Knowledge Graph Traversal")
            pipeline_html += render_pipeline_step(5, "Context Integration")
            pipeline_html += render_pipeline_step(6, "LLM Response Generation", show_connector=False)
            st.markdown(pipeline_html, unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### System Metrics")
            m1, m2 = st.columns(2)
            with m1:
                st.markdown(render_metric_card("5", "Top-K Results"), unsafe_allow_html=True)
            with m2:
                st.markdown(render_metric_card("3", "Graph Depth"), unsafe_allow_html=True)
            
            m3, m4 = st.columns(2)
            with m3:
                st.markdown(render_metric_card("384", "Vector Dim"), unsafe_allow_html=True)
            with m4:
                st.markdown(render_metric_card("✓", "GraphRAG"), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Chat Container
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        for idx, msg in enumerate(history):
            if not isinstance(msg, dict):
                continue
            
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            with st.chat_message(role, avatar="👨‍⚕️" if role == "user" else "🤖"):
                st.markdown(content)
                
                # Show GraphRAG info for assistant messages
                if role == "assistant":
                    sources = msg.get("sources", [])
                    metadata = msg.get("metadata", {})
                    graphrag_info = msg.get("graphrag_info", {}) or metadata.get("graphrag", {})
                    
                    # Status badges
                    llm_used = metadata.get("llm_used", "unknown")
                    method = graphrag_info.get("method", "RAG")
                    
                    st.markdown(f"""
                    <div style="margin-top: 1rem;">
                        {render_status_badge(f"LLM: {llm_used}", "success")}
                        {render_status_badge(f"Method: {method}", "info")}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # GraphRAG details
                    if graphrag_info and graphrag_info.get("method") == "GraphRAG":
                        with st.expander("📊 GraphRAG Details"):
                            gcol1, gcol2, gcol3 = st.columns(3)
                            with gcol1:
                                st.metric("Nodes Found", graphrag_info.get("nodes_found", 0))
                            with gcol2:
                                st.metric("Graph Edges", graphrag_info.get("edges_found", 0))
                            with gcol3:
                                st.metric("Traversal Depth", graphrag_info.get("graph_traversal_depth", 0))
                    
                    # Sources
                    if sources:
                        with st.expander(f"🔍 View Sources ({len(sources)} retrieved)"):
                            for i, source in enumerate(sources, 1):
                                st.markdown(f"""
                                <div style="background: #1A1A1A; border-left: 3px solid #C7000B; padding: 0.75rem; margin-bottom: 0.5rem; border-radius: 0 8px 8px 0;">
                                    <strong style="color: #FF6B7A;">Source {i}</strong>
                                    <p style="color: #D0D0D0; font-size: 0.85rem; margin: 0.5rem 0 0 0; white-space: pre-wrap;">{source}</p>
                                </div>
                                """, unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Describe the patient's symptoms...", key="chat_input")
    
    if user_input:
        # Update chat title on first message
        if len(history) == 0:
            words = user_input.split()
            summary = " ".join(words[:4]) + ("..." if len(words) > 4 else "")
            st.session_state.chat_titles[active] = summary
        
        # Add user message
        history.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user", avatar="👨‍⚕️"):
            st.markdown(user_input)
        
        # Generate response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔄 Processing through RAG pipeline..."):
                result = generate_medical_response(user_input)
                
                if isinstance(result, dict):
                    response_text = result["response"]
                    sources = result.get("sources", [])
                    metadata = result.get("metadata", {})
                    graphrag_info = result.get("graphrag_info", {})
                else:
                    response_text = result
                    sources = []
                    metadata = {}
                    graphrag_info = {}
            
            # Display response with typing effect
            response_placeholder = st.empty()
            typed = ""
            for word in response_text.split():
                typed += word + " "
                response_placeholder.markdown(typed)
                time.sleep(0.02)
            
            # Show metadata
            llm_used = metadata.get("llm_used", "unknown")
            method = graphrag_info.get("method", "RAG")
            
            st.markdown(f"""
            <div style="margin-top: 1rem;">
                {render_status_badge(f"LLM: {llm_used}", "success")}
                {render_status_badge(f"Method: {method}", "info")}
            </div>
            """, unsafe_allow_html=True)
            
            # GraphRAG details
            if graphrag_info and graphrag_info.get("method") == "GraphRAG":
                with st.expander("📊 GraphRAG Details"):
                    gcol1, gcol2, gcol3 = st.columns(3)
                    with gcol1:
                        st.metric("Nodes Found", graphrag_info.get("nodes_found", 0))
                    with gcol2:
                        st.metric("Graph Edges", graphrag_info.get("edges_found", 0))
                    with gcol3:
                        st.metric("Traversal Depth", graphrag_info.get("graph_traversal_depth", 0))
            
            # Sources
            if sources:
                with st.expander(f"🔍 View Sources ({len(sources)} retrieved)"):
                    for i, source in enumerate(sources, 1):
                        st.markdown(f"""
                        <div style="background: #1A1A1A; border-left: 3px solid #C7000B; padding: 0.75rem; margin-bottom: 0.5rem; border-radius: 0 8px 8px 0;">
                            <strong style="color: #FF6B7A;">Source {i}</strong>
                            <p style="color: #D0D0D0; font-size: 0.85rem; margin: 0.5rem 0 0 0; white-space: pre-wrap;">{source}</p>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Save to history
        history.append({
            "role": "assistant",
            "content": response_text,
            "sources": sources,
            "metadata": metadata,
            "graphrag_info": graphrag_info
        })
        
        st.session_state.chat_sessions[active] = history
    st.session_state.chat_last_index[active] = len(history)

# --- HELP PAGE ---
else:
    render_header("❓ Help & Documentation", "Learn how to use the Health Assistant")
    
    # How to Use
    st.markdown("### 📖 How to Use")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4 style="color: #FFFFFF;">Starting a Consultation</h4>
            <ol style="color: #D0D0D0; line-height: 2;">
                <li>Navigate to the <strong style="color: #FF6B7A;">Chat</strong> page</li>
                <li>Click <strong style="color: #FF6B7A;">➕ New Consultation</strong> to start fresh</li>
                <li>Describe the patient's symptoms in detail</li>
                <li>Review the AI-generated diagnostic suggestions</li>
                <li>Examine the sources and GraphRAG details</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4 style="color: #FFFFFF;">Best Practices</h4>
            <ul style="color: #D0D0D0; line-height: 2;">
                <li>Provide detailed symptom descriptions</li>
                <li>Include patient history when relevant</li>
                <li>Mention any existing conditions</li>
                <li>Specify duration and severity of symptoms</li>
                <li>Always verify AI suggestions professionally</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Technology Stack
    st.markdown("### 🛠️ Technology Stack")
    
    tech_cols = st.columns(4)
    
    with tech_cols[0]:
        st.markdown("""
        <div class="feature-card" style="text-align: center;">
            <div style="font-size: 2.5rem;">🧠</div>
            <h4 style="color: #FFFFFF; margin: 0.5rem 0;">Milvus</h4>
            <p style="color: #A0A0A0; font-size: 0.8rem;">Vector Database</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tech_cols[1]:
        st.markdown("""
        <div class="feature-card" style="text-align: center;">
            <div style="font-size: 2.5rem;">🤖</div>
            <h4 style="color: #FFFFFF; margin: 0.5rem 0;">DeepSeek</h4>
            <p style="color: #A0A0A0; font-size: 0.8rem;">LLM Engine</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tech_cols[2]:
        st.markdown("""
        <div class="feature-card" style="text-align: center;">
            <div style="font-size: 2.5rem;">☁️</div>
            <h4 style="color: #FFFFFF; margin: 0.5rem 0;">ModelArts</h4>
            <p style="color: #A0A0A0; font-size: 0.8rem;">AI Platform</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tech_cols[3]:
        st.markdown("""
        <div class="feature-card" style="text-align: center;">
            <div style="font-size: 2.5rem;">📦</div>
            <h4 style="color: #FFFFFF; margin: 0.5rem 0;">OBS</h4>
            <p style="color: #A0A0A0; font-size: 0.8rem;">Object Storage</p>
        </div>
        """, unsafe_allow_html=True)
    
    # FAQ
    st.markdown("### ❓ Frequently Asked Questions")
    
    with st.expander("What is GraphRAG?"):
        st.markdown("""
        **GraphRAG** (Graph-based Retrieval Augmented Generation) combines traditional vector similarity search 
        with knowledge graph traversal. This allows the system to not only find similar documents but also 
        explore related concepts and their connections, providing more comprehensive medical context.
        """)
    
    with st.expander("How accurate are the diagnoses?"):
        st.markdown("""
        The AI provides **diagnostic suggestions** based on medical knowledge, not definitive diagnoses. 
        All suggestions should be verified by qualified medical professionals. The system is designed to 
        assist, not replace, clinical decision-making.
        """)
    
    with st.expander("What data sources are used?"):
        st.markdown("""
        The system uses a curated medical knowledge base stored in Milvus, including:
        - Medical Q&A pairs
        - Clinical guidelines
        - Symptom-disease relationships
        - Treatment protocols
        """)
    
    with st.expander("Is my data secure?"):
        st.markdown("""
        Yes. The system is deployed on **Huawei Cloud** with enterprise-grade security:
        - VPC isolation
        - Encrypted data transmission
        - No persistent storage of conversation data
        - GDPR/HIPAA compliance considerations
        """)
    
    # Footer
    st.markdown(render_footer(), unsafe_allow_html=True)

    # Footer
    st.markdown(render_footer(), unsafe_allow_html=True)

