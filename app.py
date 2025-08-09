#!/usr/bin/env python3
"""
StockMate Pro - Web Interface

Modern web interface for stock photo metadata generation and upload.
Built with Streamlit for easy deployment and user interaction.

Features:
- Drag & drop image upload
- Real-time image preview
- AI metadata generation
- SEO optimization
- Platform-specific upload
- Batch processing
- Progress tracking
- Export options
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import time
import json
import zipfile
from io import BytesIO
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# Import our modules
from config import *
from stockmate_pro import EnhancedAIGenerator, Meta, TrendAnalyzer
from platform_apis import UploadManager, MockPlatformAPI, prepare_metadata_for_platform

# Page configuration
st.set_page_config(
    page_title="StockMate Pro",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .upload-area {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .error-message {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .info-box {
        background-color: #e8f4fd;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processed_images' not in st.session_state:
    st.session_state.processed_images = []

if 'upload_results' not in st.session_state:
    st.session_state.upload_results = []

if 'ai_generator' not in st.session_state:
    st.session_state.ai_generator = None

# Header
st.markdown('<h1 class="main-header">📸 StockMate Pro</h1>', unsafe_allow_html=True)
st.markdown("### AI-Powered Stock Photo Metadata & Upload Tool")

# Sidebar navigation
with st.sidebar:
    selected = option_menu(
        "Main Menu",
        ["🏠 Home", "📤 Upload & Process", "🔍 SEO Analysis", "🚀 Platform Upload", "📊 Analytics", "⚙️ Settings"],
        icons=['house', 'cloud-upload', 'search', 'rocket', 'bar-chart', 'gear'],
        menu_icon="cast",
        default_index=0,
    )

# Home Page
if selected == "🏠 Home":
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🤖 AI-Powered Analysis</h3>
            <p>Advanced GPT-4o image analysis with intelligent keyword generation</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📈 SEO Optimization</h3>
            <p>Market trend analysis and keyword optimization for maximum visibility</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>🌐 Multi-Platform</h3>
            <p>Direct upload to Shutterstock, Adobe Stock, and Getty Images</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick stats
    if st.session_state.processed_images:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Images Processed", len(st.session_state.processed_images))
        
        with col2:
            avg_seo = np.mean([img.get('seo_score', 0) for img in st.session_state.processed_images])
            st.metric("Avg SEO Score", f"{avg_seo:.2f}")
        
        with col3:
            high_potential = sum(1 for img in st.session_state.processed_images 
                               if img.get('market_potential') == 'High')
            st.metric("High Potential Images", high_potential)
        
        with col4:
            total_keywords = sum(len(img.get('keywords', [])) 
                               for img in st.session_state.processed_images)
            st.metric("Total Keywords Generated", total_keywords)
    
    # Features overview
    st.markdown("### 🚀 Key Features")
    
    features = [
        "🧠 **Smart AI Analysis**: GPT-4o powered image understanding and metadata generation",
        "🎯 **SEO Optimization**: Market trend integration and keyword ranking optimization", 
        "📱 **Modern Interface**: Drag & drop uploads with real-time preview",
        "🔄 **Batch Processing**: Handle hundreds of images efficiently",
        "📊 **Analytics Dashboard**: Track performance and optimize strategies",
        "🌍 **Multi-language**: English and Chinese keyword support",
        "💾 **IPTC Embedding**: Automatic metadata writing to image files",
        "📋 **CSV Export**: Ready-to-upload files for all major platforms"
    ]
    
    for feature in features:
        st.markdown(f"- {feature}")

# Upload & Process Page
elif selected == "📤 Upload & Process":
    st.markdown("### 📤 Upload & Process Images")
    
    # Configuration section
    with st.expander("⚙️ Processing Configuration", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            target_platform = st.selectbox(
                "Target Platform",
                ["shutterstock", "adobe_stock", "getty_images"],
                help="Choose your target platform for optimized metadata"
            )
        
        with col2:
            enable_seo = st.checkbox(
                "Enable SEO Optimization",
                value=True,
                help="Use market trends and keyword analysis for better ranking"
            )
        
        with col3:
            max_keywords = st.slider(
                "Max Keywords",
                min_value=10,
                max_value=50,
                value=30,
                help="Maximum number of keywords to generate per image"
            )
        
        col4, col5 = st.columns(2)
        
        with col4:
            ai_model = st.selectbox(
                "AI Model",
                ["gpt-4o-mini", "gpt-4o", "gpt-4-vision-preview"],
                help="Choose the AI model for analysis"
            )
        
        with col5:
            language = st.selectbox(
                "Language",
                ["en", "zh", "en,zh"],
                index=2,
                help="Keyword languages to generate"
            )
    
    # File upload section
    st.markdown("### 📁 Upload Images")
    
    uploaded_files = st.file_uploader(
        "Choose image files",
        type=['jpg', 'jpeg', 'png', 'tiff', 'tif'],
        accept_multiple_files=True,
        help="Drag and drop or click to select multiple images"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} files uploaded successfully!")
        
        # Preview uploaded images
        if st.checkbox("Show image previews"):
            cols = st.columns(min(4, len(uploaded_files)))
            for idx, uploaded_file in enumerate(uploaded_files[:4]):
                with cols[idx % 4]:
                    image = Image.open(uploaded_file)
                    st.image(image, caption=uploaded_file.name, use_column_width=True)
                    st.caption(f"Size: {image.size[0]}x{image.size[1]}")
        
        # Process button
        if st.button("🚀 Process Images", type="primary"):
            # Initialize AI generator
            if not st.session_state.ai_generator:
                try:
                    st.session_state.ai_generator = EnhancedAIGenerator(
                        model=ai_model,
                        temperature=0.2
                    )
                except Exception as e:
                    st.error(f"❌ Failed to initialize AI generator: {e}")
                    st.stop()
            
            # Process images
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            processed_data = []
            
            for idx, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name}...")
                
                try:
                    # Save uploaded file temporarily
                    temp_path = UPLOADS_DIR / uploaded_file.name
                    with open(temp_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Generate metadata
                    meta = st.session_state.ai_generator.for_image(
                        temp_path,
                        platform=target_platform,
                        optimize_seo=enable_seo,
                        max_kw=max_keywords
                    )
                    
                    # Prepare data for display
                    keywords = meta.merged_keywords(language, max_keywords)
                    
                    image_data = {
                        'filename': uploaded_file.name,
                        'title': meta.title,
                        'description': meta.description,
                        'keywords': keywords,
                        'category': meta.category,
                        'seo_score': meta.seo_score,
                        'market_potential': meta.market_potential,
                        'trending_keywords': meta.trending_keywords,
                        'color_tags': meta.color_tags,
                        'mood_tags': meta.mood_tags,
                        'style_tags': meta.style_tags,
                        'meta_object': meta  # Store full meta object
                    }
                    
                    processed_data.append(image_data)
                    
                    # Clean up temp file
                    temp_path.unlink()
                    
                except Exception as e:
                    st.error(f"❌ Error processing {uploaded_file.name}: {e}")
                
                # Update progress
                progress_bar.progress((idx + 1) / len(uploaded_files))
            
            status_text.text("✅ Processing complete!")
            
            # Store in session state
            st.session_state.processed_images.extend(processed_data)
            
            # Display results
            if processed_data:
                st.markdown("### 📊 Processing Results")
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_seo = np.mean([img['seo_score'] for img in processed_data])
                    st.metric("Avg SEO Score", f"{avg_seo:.2f}")
                
                with col2:
                    high_potential = sum(1 for img in processed_data 
                                       if img['market_potential'] == 'High')
                    st.metric("High Potential", f"{high_potential}/{len(processed_data)}")
                
                with col3:
                    total_keywords = sum(len(img['keywords']) for img in processed_data)
                    st.metric("Total Keywords", total_keywords)
                
                with col4:
                    avg_keywords = total_keywords / len(processed_data) if processed_data else 0
                    st.metric("Avg Keywords/Image", f"{avg_keywords:.1f}")
                
                # Detailed results table
                st.markdown("### 📋 Detailed Results")
                
                # Create DataFrame for display
                display_data = []
                for img in processed_data:
                    display_data.append({
                        'Filename': img['filename'],
                        'Title': img['title'][:50] + '...' if len(img['title']) > 50 else img['title'],
                        'Category': img['category'],
                        'SEO Score': f"{img['seo_score']:.2f}",
                        'Market Potential': img['market_potential'],
                        'Keywords Count': len(img['keywords']),
                        'Trending Keywords': len(img['trending_keywords'])
                    })
                
                df = pd.DataFrame(display_data)
                st.dataframe(df, use_container_width=True)
                
                # Export options
                st.markdown("### 💾 Export Options")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📋 Export CSV"):
                        # Prepare CSV data
                        csv_data = []
                        for img in processed_data:
                            csv_data.append({
                                'filename': img['filename'],
                                'title': img['title'],
                                'description': img['description'],
                                'keywords': '; '.join(img['keywords']),
                                'category': img['category'],
                                'seo_score': img['seo_score'],
                                'market_potential': img['market_potential']
                            })
                        
                        csv_df = pd.DataFrame(csv_data)
                        csv_buffer = BytesIO()
                        csv_df.to_csv(csv_buffer, index=False)
                        
                        st.download_button(
                            label="⬇️ Download CSV",
                            data=csv_buffer.getvalue(),
                            file_name=f"stockmate_export_{int(time.time())}.csv",
                            mime="text/csv"
                        )
                
                with col2:
                    if st.button("📄 Export JSON"):
                        # Prepare JSON data
                        json_data = {
                            'export_timestamp': time.time(),
                            'platform': target_platform,
                            'settings': {
                                'seo_enabled': enable_seo,
                                'max_keywords': max_keywords,
                                'language': language
                            },
                            'images': processed_data
                        }
                        
                        json_str = json.dumps(json_data, indent=2, default=str)
                        
                        st.download_button(
                            label="⬇️ Download JSON",
                            data=json_str,
                            file_name=f"stockmate_export_{int(time.time())}.json",
                            mime="application/json"
                        )

# SEO Analysis Page
elif selected == "🔍 SEO Analysis":
    st.markdown("### 🔍 SEO Analysis & Optimization")
    
    if not st.session_state.processed_images:
        st.info("📝 No processed images found. Please upload and process some images first.")
    else:
        # SEO Overview
        st.markdown("### 📊 SEO Performance Overview")
        
        # Calculate SEO metrics
        seo_scores = [img['seo_score'] for img in st.session_state.processed_images]
        market_potential = [img['market_potential'] for img in st.session_state.processed_images]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # SEO Score Distribution
            fig_seo = px.histogram(
                x=seo_scores,
                nbins=20,
                title="SEO Score Distribution",
                labels={'x': 'SEO Score', 'y': 'Number of Images'}
            )
            fig_seo.update_layout(showlegend=False)
            st.plotly_chart(fig_seo, use_container_width=True)
        
        with col2:
            # Market Potential Distribution
            potential_counts = pd.Series(market_potential).value_counts()
            fig_potential = px.pie(
                values=potential_counts.values,
                names=potential_counts.index,
                title="Market Potential Distribution"
            )
            st.plotly_chart(fig_potential, use_container_width=True)
        
        # Keyword Analysis
        st.markdown("### 🔑 Keyword Analysis")
        
        # Collect all keywords
        all_keywords = []
        trending_keywords = []
        
        for img in st.session_state.processed_images:
            all_keywords.extend(img['keywords'])
            trending_keywords.extend(img['trending_keywords'])
        
        # Keyword frequency analysis
        keyword_freq = pd.Series(all_keywords).value_counts().head(20)
        trending_freq = pd.Series(trending_keywords).value_counts().head(10)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Top Keywords")
            fig_keywords = px.bar(
                x=keyword_freq.values,
                y=keyword_freq.index,
                orientation='h',
                title="Most Frequent Keywords"
            )
            fig_keywords.update_layout(height=500)
            st.plotly_chart(fig_keywords, use_container_width=True)
        
        with col2:
            st.markdown("#### Trending Keywords")
            if len(trending_freq) > 0:
                fig_trending = px.bar(
                    x=trending_freq.values,
                    y=trending_freq.index,
                    orientation='h',
                    title="Most Used Trending Keywords"
                )
                fig_trending.update_layout(height=500)
                st.plotly_chart(fig_trending, use_container_width=True)
            else:
                st.info("No trending keywords found in processed images.")
        
        # SEO Recommendations
        st.markdown("### 💡 SEO Recommendations")
        
        low_seo_images = [img for img in st.session_state.processed_images if img['seo_score'] < 0.6]
        
        if low_seo_images:
            st.warning(f"⚠️ {len(low_seo_images)} images have SEO scores below 0.6")
            
            with st.expander("View low-scoring images"):
                for img in low_seo_images[:5]:  # Show first 5
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.metric("SEO Score", f"{img['seo_score']:.2f}")
                    with col2:
                        st.write(f"**{img['filename']}**")
                        st.write(f"Title: {img['title']}")
                        st.write(f"Keywords: {len(img['keywords'])}")
        
        # Improvement suggestions
        recommendations = []
        
        if np.mean(seo_scores) < 0.7:
            recommendations.append("📝 Consider adding more descriptive titles (30-60 characters optimal)")
        
        if any(len(img['keywords']) < 20 for img in st.session_state.processed_images):
            recommendations.append("🏷️ Add more keywords to images with fewer than 20 keywords")
        
        if sum(1 for img in st.session_state.processed_images if img['trending_keywords']) < len(st.session_state.processed_images) * 0.5:
            recommendations.append("🔥 Include more trending keywords to boost discoverability")
        
        if recommendations:
            st.markdown("#### 🎯 Improvement Suggestions")
            for rec in recommendations:
                st.markdown(f"- {rec}")

# Platform Upload Page
elif selected == "🚀 Platform Upload":
    st.markdown("### 🚀 Platform Upload")
    
    if not st.session_state.processed_images:
        st.info("📝 No processed images found. Please upload and process some images first.")
    else:
        # Platform configuration
        st.markdown("### ⚙️ Platform Configuration")
        
        # Create upload manager
        upload_manager = UploadManager()
        
        # Check platform status
        col1, col2, col3 = st.columns(3)
        
        platforms_status = {
            "shutterstock": upload_manager.get_platform_status("shutterstock"),
            "adobe_stock": upload_manager.get_platform_status("adobe_stock"),
            "getty_images": upload_manager.get_platform_status("getty_images")
        }
        
        with col1:
            status = platforms_status["shutterstock"]
            if status["configured"]:
                st.success("✅ Shutterstock: Configured")
                if status["authenticated"]:
                    st.success("🔐 Authentication: OK")
                else:
                    st.warning("🔐 Authentication: Failed")
            else:
                st.error("❌ Shutterstock: Not configured")
        
        with col2:
            status = platforms_status["adobe_stock"]
            if status["configured"]:
                st.success("✅ Adobe Stock: Configured")
                if status["authenticated"]:
                    st.success("🔐 Authentication: OK")
                else:
                    st.warning("🔐 Authentication: Failed")
            else:
                st.error("❌ Adobe Stock: Not configured")
        
        with col3:
            status = platforms_status["getty_images"]
            if status["configured"]:
                st.success("✅ Getty Images: Configured")
            else:
                st.error("❌ Getty Images: Not configured")
        
        # Upload configuration
        st.markdown("### 📤 Upload Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_platforms = st.multiselect(
                "Select platforms to upload to",
                ["shutterstock", "adobe_stock", "getty_images"],
                default=["shutterstock"],
                help="Choose which platforms to upload to"
            )
        
        with col2:
            demo_mode = st.checkbox(
                "Demo Mode",
                value=True,
                help="Use mock uploads for demonstration (no real API calls)"
            )
        
        # Image selection
        st.markdown("### 📋 Select Images to Upload")
        
        # Create DataFrame for selection
        selection_data = []
        for idx, img in enumerate(st.session_state.processed_images):
            selection_data.append({
                'Select': False,
                'Filename': img['filename'],
                'Title': img['title'][:40] + '...' if len(img['title']) > 40 else img['title'],
                'SEO Score': f"{img['seo_score']:.2f}",
                'Market Potential': img['market_potential'],
                'Keywords': len(img['keywords']),
                'Index': idx
            })
        
        if selection_data:
            # Use data editor for selection
            edited_df = st.data_editor(
                pd.DataFrame(selection_data),
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select images to upload",
                        default=False,
                    )
                },
                disabled=["Filename", "Title", "SEO Score", "Market Potential", "Keywords", "Index"],
                hide_index=True,
                use_container_width=True
            )
            
            # Get selected images
            selected_indices = edited_df[edited_df['Select']]['Index'].tolist()
            selected_images = [st.session_state.processed_images[i] for i in selected_indices]
            
            if selected_images and selected_platforms:
                st.success(f"✅ {len(selected_images)} images selected for upload to {', '.join(selected_platforms)}")
                
                # Upload button
                if st.button("🚀 Start Upload", type="primary"):
                    
                    if demo_mode:
                        st.info("📝 Running in demo mode - using mock uploads")
                        
                        # Use mock API for demo
                        from platform_apis import MockPlatformAPI
                        
                        upload_results = []
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        total_uploads = len(selected_images) * len(selected_platforms)
                        current_upload = 0
                        
                        for img in selected_images:
                            for platform in selected_platforms:
                                status_text.text(f"Uploading {img['filename']} to {platform}...")
                                
                                # Create mock API
                                mock_api = MockPlatformAPI(platform)
                                
                                # Prepare metadata
                                metadata = prepare_metadata_for_platform({
                                    'title': img['title'],
                                    'description': img['description'],
                                    'keywords': img['keywords'],
                                    'category': img['category']
                                }, platform)
                                
                                # Mock upload (no real file needed for demo)
                                result = mock_api.upload_image(Path(img['filename']), metadata)
                                upload_results.append(result)
                                
                                current_upload += 1
                                progress_bar.progress(current_upload / total_uploads)
                        
                        status_text.text("✅ Upload simulation complete!")
                        st.session_state.upload_results = upload_results
                        
                        # Display results
                        st.markdown("### 📊 Upload Results")
                        
                        success_count = sum(1 for r in upload_results if r.success)
                        failure_count = len(upload_results) - success_count
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Uploads", len(upload_results))
                        with col2:
                            st.metric("Successful", success_count)
                        with col3:
                            st.metric("Failed", failure_count)
                        
                        # Detailed results
                        results_data = []
                        for result in upload_results:
                            results_data.append({
                                'Filename': result.filename,
                                'Platform': result.platform.title(),
                                'Status': '✅ Success' if result.success else '❌ Failed',
                                'Upload ID': result.upload_id or 'N/A',
                                'Error': result.error_message or 'None'
                            })
                        
                        results_df = pd.DataFrame(results_data)
                        st.dataframe(results_df, use_container_width=True)
                    
                    else:
                        st.error("❌ Real upload mode requires valid API credentials in the .env file")
            
            else:
                if not selected_images:
                    st.warning("⚠️ Please select images to upload")
                if not selected_platforms:
                    st.warning("⚠️ Please select at least one platform")

# Analytics Page
elif selected == "📊 Analytics":
    st.markdown("### 📊 Analytics Dashboard")
    
    if not st.session_state.processed_images:
        st.info("📝 No data available. Please process some images first.")
    else:
        # Analytics overview
        images_data = st.session_state.processed_images
        
        # Key metrics
        st.markdown("### 🎯 Key Performance Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_images = len(images_data)
            st.metric("Total Images", total_images)
        
        with col2:
            avg_seo = np.mean([img['seo_score'] for img in images_data])
            st.metric("Avg SEO Score", f"{avg_seo:.2f}")
        
        with col3:
            high_potential = sum(1 for img in images_data if img['market_potential'] == 'High')
            st.metric("High Potential Images", f"{high_potential}/{total_images}")
        
        with col4:
            total_keywords = sum(len(img['keywords']) for img in images_data)
            st.metric("Total Keywords Generated", total_keywords)
        
        # Performance distribution
        st.markdown("### 📈 Performance Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # SEO Score vs Keywords count
            seo_scores = [img['seo_score'] for img in images_data]
            keyword_counts = [len(img['keywords']) for img in images_data]
            
            fig_scatter = px.scatter(
                x=keyword_counts,
                y=seo_scores,
                title="SEO Score vs Keyword Count",
                labels={'x': 'Number of Keywords', 'y': 'SEO Score'}
            )
            fig_scatter.add_hline(y=0.7, line_dash="dash", line_color="red", 
                                 annotation_text="Good SEO Threshold")
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with col2:
            # Category distribution
            categories = [img['category'] for img in images_data if img['category']]
            if categories:
                category_counts = pd.Series(categories).value_counts()
                fig_categories = px.bar(
                    x=category_counts.index,
                    y=category_counts.values,
                    title="Images by Category"
                )
                fig_categories.update_xaxes(tickangle=45)
                st.plotly_chart(fig_categories, use_container_width=True)
            else:
                st.info("No category data available")
        
        # Trend analysis
        if len(images_data) > 1:
            st.markdown("### 🔍 Trend Analysis")
            
            # Use TrendAnalyzer
            try:
                analyzer = TrendAnalyzer()
                # Convert our data to Meta objects for analysis
                meta_objects = []
                for img in images_data:
                    if 'meta_object' in img:
                        meta_objects.append(img['meta_object'])
                
                if meta_objects:
                    trends = analyzer.analyze_batch_trends(meta_objects)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 🔥 Top Trending Keywords")
                        top_trends = list(trends['trend_scores'].items())[:10]
                        trend_df = pd.DataFrame(top_trends, columns=['Keyword', 'Trend Score'])
                        trend_df['Trend Score'] = trend_df['Trend Score'].round(3)
                        st.dataframe(trend_df, use_container_width=True)
                    
                    with col2:
                        st.markdown("#### 📊 Market Potential Analysis")
                        potential_dist = trends['market_potential_distribution']
                        
                        fig_potential_trend = px.pie(
                            values=list(potential_dist.values()),
                            names=list(potential_dist.keys()),
                            title="Market Potential Distribution"
                        )
                        st.plotly_chart(fig_potential_trend, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error in trend analysis: {e}")
        
        # Export analytics
        if st.button("📊 Export Analytics Report"):
            # Create comprehensive report
            report_data = {
                'summary': {
                    'total_images': len(images_data),
                    'avg_seo_score': np.mean([img['seo_score'] for img in images_data]),
                    'high_potential_count': sum(1 for img in images_data if img['market_potential'] == 'High'),
                    'total_keywords': sum(len(img['keywords']) for img in images_data)
                },
                'detailed_analysis': images_data
            }
            
            report_json = json.dumps(report_data, indent=2, default=str)
            
            st.download_button(
                label="⬇️ Download Analytics Report",
                data=report_json,
                file_name=f"stockmate_analytics_{int(time.time())}.json",
                mime="application/json"
            )

# Settings Page
elif selected == "⚙️ Settings":
    st.markdown("### ⚙️ Settings & Configuration")
    
    # API Configuration
    st.markdown("### 🔑 API Configuration")
    
    with st.expander("OpenAI API Settings", expanded=True):
        api_key_status = "✅ Configured" if OPENAI_API_KEY else "❌ Not configured"
        st.write(f"OpenAI API Key: {api_key_status}")
        
        if not OPENAI_API_KEY:
            st.error("⚠️ OpenAI API key is required for AI-powered analysis")
            st.code("export OPENAI_API_KEY=your_api_key_here")
    
    with st.expander("Platform API Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Shutterstock API**")
            shutterstock_status = "✅ Configured" if SHUTTERSTOCK_API_KEY else "❌ Not configured"
            st.write(f"Status: {shutterstock_status}")
        
        with col2:
            st.write("**Adobe Stock API**")
            adobe_status = "✅ Configured" if ADOBE_STOCK_API_KEY else "❌ Not configured"
            st.write(f"Status: {adobe_status}")
    
    # Processing Settings
    st.markdown("### ⚙️ Processing Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Default Values**")
        st.info(f"Max Keywords: {MAX_KEYWORDS_DEFAULT}")
        st.info(f"Default Language: {DEFAULT_LANGUAGE}")
        st.info(f"Default Model: {DEFAULT_MODEL}")
    
    with col2:
        st.write("**File Limits**")
        st.info(f"Max File Size: {MAX_FILE_SIZE_MB} MB")
        st.info(f"Supported Formats: {', '.join(SUPPORTED_FORMATS)}")
    
    # Clear Data
    st.markdown("### 🗑️ Data Management")
    
    if st.session_state.processed_images:
        st.write(f"Currently storing {len(st.session_state.processed_images)} processed images")
        
        if st.button("🗑️ Clear All Data", type="secondary"):
            st.session_state.processed_images = []
            st.session_state.upload_results = []
            st.success("✅ All data cleared!")
            st.rerun()
    else:
        st.info("No data to clear")
    
    # About
    st.markdown("### ℹ️ About StockMate Pro")
    
    st.markdown("""
    **StockMate Pro v1.0**
    
    Advanced AI-powered stock photo metadata generation and upload tool.
    
    **Features:**
    - 🤖 GPT-4o powered image analysis
    - 🎯 SEO optimization with market trends
    - 📤 Multi-platform upload support
    - 📊 Advanced analytics and reporting
    - 🌍 Multi-language keyword generation
    
    **Supported Platforms:**
    - Shutterstock
    - Adobe Stock
    - Getty Images
    
    **Built with:**
    - Python 3.8+
    - Streamlit
    - OpenAI GPT-4o
    - Plotly for visualizations
    """)

# Footer
st.markdown("---")
st.markdown(
    "**StockMate Pro** - Built with ❤️ using Streamlit | "
    "🤖 Powered by OpenAI GPT-4o"
)