#!/usr/bin/env python3
import os
import sys
import time
import psycopg2
import requests
import json
from datetime import datetime

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def test_postgres():
    log("Testing PostgreSQL connectivity...")
    
    try:
        host = os.environ.get('PGHOST')
        port = os.environ.get('PGPORT', '5432')
        database = os.environ.get('PGDATABASE')
        user = os.environ.get('PGUSER')
        password = os.environ.get('PGPASSWORD')
        
        log(f"Connecting to PostgreSQL at {host}:{port}/{database}")
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        log(f"PostgreSQL connection successful! Version: {version[0]}")
        
        # List all databases
        log("Listing available databases...")
        cursor.execute("""
            SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
            FROM pg_database 
            WHERE datistemplate = false 
            ORDER BY datname;
        """)
        databases = cursor.fetchall()
        
        log(f"Found {len(databases)} databases:")
        for db_name, db_size in databases:
            log(f"  - {db_name} ({db_size})")
        
        cursor.close()
        conn.close()
        
        # Test extensions for each database
        test_postgres_extensions()
        
        return True
        
    except Exception as e:
        log(f"PostgreSQL connection failed: {str(e)}", "ERROR")
        return False

def test_postgres_extensions():
    log("Testing PostgreSQL extensions for each database...")
    
    try:
        host = os.environ.get('PGHOST')
        port = os.environ.get('PGPORT', '5432')
        user = os.environ.get('PGUSER')
        password = os.environ.get('PGPASSWORD')
        
        # First, get list of accessible databases
        conn = psycopg2.connect(
            host=host,
            port=port,
            database='postgres',  # Connect to default postgres database
            user=user,
            password=password,
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT datname 
            FROM pg_database 
            WHERE datistemplate = false 
            AND has_database_privilege(current_user, datname, 'CONNECT')
            ORDER BY datname;
        """)
        databases = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        log(f"Checking extensions in {len(databases)} accessible databases...")
        
        for db_name in databases:
            try:
                log(f"Database: {db_name}")
                log("-" * 40)
                
                # Connect to specific database
                db_conn = psycopg2.connect(
                    host=host,
                    port=port,
                    database=db_name,
                    user=user,
                    password=password,
                    connect_timeout=10
                )
                
                db_cursor = db_conn.cursor()
                
                # Get installed extensions
                db_cursor.execute("""
                    SELECT 
                        extname as extension_name,
                        extversion as version,
                        nspname as schema
                    FROM pg_extension e
                    JOIN pg_namespace n ON n.oid = e.extnamespace
                    ORDER BY extname;
                """)
                extensions = db_cursor.fetchall()
                
                if extensions:
                    log(f"  Extensions ({len(extensions)} installed):")
                    for ext_name, ext_version, ext_schema in extensions:
                        log(f"    • {ext_name} v{ext_version} (schema: {ext_schema})")
                else:
                    log("    No extensions installed")
                
                # Get available (but not installed) extensions
                db_cursor.execute("""
                    SELECT 
                        name,
                        default_version,
                        comment
                    FROM pg_available_extensions
                    WHERE name NOT IN (SELECT extname FROM pg_extension)
                    ORDER BY name
                    LIMIT 10;
                """)
                available = db_cursor.fetchall()
                
                if available:
                    log(f"  Available extensions (showing first 10):")
                    for ext_name, ext_version, ext_comment in available:
                        comment_short = ext_comment[:50] + "..." if ext_comment and len(ext_comment) > 50 else ext_comment or "No description"
                        log(f"    • {ext_name} v{ext_version} - {comment_short}")
                
                db_cursor.close()
                db_conn.close()
                
                log("")  # Empty line between databases
                
            except Exception as db_error:
                log(f"    Error accessing database {db_name}: {str(db_error)}", "WARN")
                continue
        
    except Exception as e:
        log(f"PostgreSQL extensions check failed: {str(e)}", "ERROR")

def test_azure_openai():
    log("Testing Azure OpenAI connectivity...")
    
    endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
    api_key = os.environ.get('AZURE_OPENAI_API_KEY')
    deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT')
    api_version = os.environ.get('AZURE_OPENAI_API_VERSION', '2024-02-01')
    
    if not all([endpoint, api_key, deployment]):
        log("Azure OpenAI test skipped - missing configuration", "WARN")
        return None
    
    try:
        url = f"{endpoint}/openai/deployments/{deployment}/completions?api-version={api_version}"
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": "Hello",
            "max_tokens": 5,
            "temperature": 0
        }
        
        log(f"Testing Azure OpenAI endpoint: {endpoint}")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            log("Azure OpenAI connection successful!")
            return True
        else:
            log(f"Azure OpenAI connection failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
            return False
            
    except Exception as e:
        log(f"Azure OpenAI connection error: {str(e)}", "ERROR")
        return False

def test_azure_document_intelligence():
    log("Testing Azure Document Intelligence connectivity...")
    
    endpoint = os.environ.get('AZURE_DOCINTEL_ENDPOINT')
    api_key = os.environ.get('AZURE_DOCINTEL_API_KEY')
    api_version = os.environ.get('AZURE_DOCINTEL_API_VERSION', '2023-07-31')
    
    if not all([endpoint, api_key]):
        log("Azure Document Intelligence test skipped - missing configuration", "WARN")
        return None
    
    try:
        # Test with a simple health check endpoint
        url = f"{endpoint}/formrecognizer/documentModels?api-version={api_version}"
        headers = {
            "Ocp-Apim-Subscription-Key": api_key
        }
        
        log(f"Testing Azure Document Intelligence endpoint: {endpoint}")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            log("Azure Document Intelligence connection successful!")
            return True
        else:
            log(f"Azure Document Intelligence connection failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
            return False
            
    except Exception as e:
        log(f"Azure Document Intelligence connection error: {str(e)}", "ERROR")
        return False

def test_persistent_volume():
    log("Testing Persistent Volume Claim (PVC)...")
    
    # Check if PVC is enabled
    pvc_enabled = os.environ.get('TEST_PVC', 'false').lower() == 'true'
    if not pvc_enabled:
        log("PVC test skipped - not enabled (set TEST_PVC=true to enable)", "WARN")
        return None
    
    mount_path = os.environ.get('PVC_MOUNT_PATH', '/mnt/test-storage')
    
    try:
        # Test 1: Check if mount path exists
        if not os.path.exists(mount_path):
            log(f"PVC mount path does not exist: {mount_path}", "ERROR")
            return False
        
        log(f"PVC mount path exists: {mount_path}")
        
        # Test 2: Check if directory is writable
        test_file = os.path.join(mount_path, 'test-write.txt')
        test_content = f"PVC write test at {datetime.now()}"
        
        log("Testing write permissions...")
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Test 3: Check if we can read the file back
        log("Testing read permissions...")
        with open(test_file, 'r') as f:
            read_content = f.read()
        
        if read_content != test_content:
            log("PVC read/write content mismatch", "ERROR")
            return False
        
        log("PVC read/write test successful")
        
        # Test 4: Check storage info
        import shutil
        total, used, free = shutil.disk_usage(mount_path)
        log(f"PVC storage info - Total: {total//1024//1024}MB, Used: {used//1024//1024}MB, Free: {free//1024//1024}MB")
        
        # Test 5: Test file persistence (create marker file)
        marker_file = os.path.join(mount_path, 'pvc-test-marker.txt')
        with open(marker_file, 'w') as f:
            f.write(f"PVC test marker created at {datetime.now()}")
        log(f"Created persistence marker file: {marker_file}")
        
        # Clean up test file (but keep marker)
        os.remove(test_file)
        
        log("PVC tests completed successfully!")
        return True
        
    except Exception as e:
        log(f"PVC test failed: {str(e)}", "ERROR")
        return False

def test_ollama():
    log("Testing Ollama connectivity...")
    
    endpoint = os.environ.get('OLLAMA_ENDPOINT')
    model = os.environ.get('OLLAMA_MODEL', 'llama2')
    
    if not endpoint:
        log("Ollama test skipped - missing OLLAMA_ENDPOINT", "WARN")
        return None
    
    try:
        # Test Ollama API endpoint
        url = f"{endpoint}/api/generate"
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "prompt": "Hello",
            "stream": False,
            "options": {
                "num_predict": 5
            }
        }
        
        log(f"Testing Ollama endpoint: {endpoint} with model: {model}")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            log("Ollama connection successful!")
            return True
        else:
            log(f"Ollama connection failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
            return False
            
    except Exception as e:
        log(f"Ollama connection error: {str(e)}", "ERROR")
        return False

def test_openai_compatible():
    log("Testing OpenAI-compatible endpoint...")
    
    endpoint = os.environ.get('OPENAI_COMPATIBLE_ENDPOINT')
    api_key = os.environ.get('OPENAI_COMPATIBLE_API_KEY')
    model = os.environ.get('OPENAI_COMPATIBLE_MODEL', 'gpt-3.5-turbo')
    
    if not endpoint:
        log("OpenAI-compatible test skipped - missing OPENAI_COMPATIBLE_ENDPOINT", "WARN")
        return None
    
    try:
        # Test OpenAI-compatible API endpoint
        url = f"{endpoint}/v1/completions"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add authorization header if API key is provided
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "model": model,
            "prompt": "Hello",
            "max_tokens": 5,
            "temperature": 0
        }
        
        log(f"Testing OpenAI-compatible endpoint: {endpoint} with model: {model}")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            log("OpenAI-compatible connection successful!")
            return True
        else:
            # Try chat completions endpoint as fallback
            log("Trying chat completions endpoint...")
            url = f"{endpoint}/v1/chat/completions"
            chat_payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5,
                "temperature": 0
            }
            
            response = requests.post(url, headers=headers, json=chat_payload, timeout=30)
            
            if response.status_code == 200:
                log("OpenAI-compatible connection successful (chat endpoint)!")
                return True
            else:
                log(f"OpenAI-compatible connection failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
            
    except Exception as e:
        log(f"OpenAI-compatible connection error: {str(e)}", "ERROR")
        return False

def test_custom_hostnames():
    log("Testing connectivity to custom hostnames...")
    
    # Check if custom hostname tests are enabled
    test_enabled = os.environ.get('TEST_CUSTOM_HOSTNAMES', 'true').lower() == 'true'
    if not test_enabled:
        log("Custom hostname tests skipped - disabled (set TEST_CUSTOM_HOSTNAMES=true to enable)", "WARN")
        return None
    
    # Get custom hostnames from environment variables
    custom_hosts = {}
    for i in range(1, 11):  # Support up to 10 custom hosts
        host_key = f'CUSTOM_HOST_{i}'
        name_key = f'CUSTOM_HOST_{i}_NAME'
        
        host_url = os.environ.get(host_key, '').strip()
        host_name = os.environ.get(name_key, f'Custom Host {i}').strip()
        
        if host_url:
            custom_hosts[host_name] = host_url
    
    if not custom_hosts:
        log("No custom hostnames configured - skipping (configure CUSTOM_HOST_1, CUSTOM_HOST_2, etc.)", "WARN")
        return None
    
    results = {}
    
    for service_name, url in custom_hosts.items():
        try:
            log(f"Testing {service_name} connectivity to {url}...")
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                # Try HTTPS first, then HTTP if it fails
                test_urls = [f'https://{url}', f'http://{url}']
            else:
                test_urls = [url]
            
            success = False
            final_status = None
            
            for test_url in test_urls:
                try:
                    response = requests.get(test_url, timeout=10, allow_redirects=True)
                    final_status = response.status_code
                    
                    # Consider 2xx and 3xx status codes as successful
                    if response.status_code < 400:
                        log(f"{service_name}: REACHABLE (Status: {response.status_code}, URL: {test_url})")
                        results[service_name] = True
                        success = True
                        break
                    else:
                        log(f"{service_name}: HTTP {response.status_code} for {test_url}")
                        
                except requests.exceptions.SSLError:
                    log(f"{service_name}: SSL Error for {test_url}, trying HTTP if available")
                    continue
                except requests.exceptions.ConnectionError:
                    log(f"{service_name}: Connection Error for {test_url}")
                    continue
                except Exception as e:
                    log(f"{service_name}: Error for {test_url} - {str(e)}")
                    continue
            
            if not success:
                if final_status:
                    log(f"{service_name}: UNREACHABLE (Final Status: {final_status})", "WARN")
                else:
                    log(f"{service_name}: UNREACHABLE (Connection failed)", "WARN")
                results[service_name] = False
                
        except Exception as e:
            log(f"{service_name}: ERROR - {str(e)}", "WARN")
            results[service_name] = False
    
    # Summary of custom hostname tests
    reachable = sum(1 for v in results.values() if v)
    total = len(results)
    log(f"Custom hostnames summary: {reachable}/{total} hosts reachable")
    
    return results

def test_external_services():
    log("Testing connectivity to external services...")
    
    # Check if external service tests are enabled
    test_enabled = os.environ.get('TEST_EXTERNAL_SERVICES', 'true').lower() == 'true'
    if not test_enabled:
        log("External service tests skipped - disabled (set TEST_EXTERNAL_SERVICES=true to enable)", "WARN")
        return None
    
    services = {
        'Office 365': 'https://login.microsoftonline.com',
        'Google Drive': 'https://accounts.google.com',
        'Notion': 'https://www.notion.so',
        'Box': 'https://account.box.com',
        'Dropbox': 'https://www.dropbox.com',
        'ServiceNow': 'https://www.servicenow.com',
        'Amazon S3': 'https://aws.amazon.com/s3/',
        'Confluence': 'https://www.atlassian.com/software/confluence'
    }
    
    results = {}
    
    for service_name, url in services.items():
        try:
            log(f"Testing {service_name} connectivity...")
            response = requests.get(url, timeout=10, allow_redirects=True)
            
            # Consider 2xx and 3xx status codes as successful
            if response.status_code < 400:
                log(f"{service_name}: REACHABLE (Status: {response.status_code})")
                results[service_name] = True
            else:
                log(f"{service_name}: UNREACHABLE (Status: {response.status_code})", "WARN")
                results[service_name] = False
                
        except requests.exceptions.Timeout:
            log(f"{service_name}: TIMEOUT (10s)", "WARN")
            results[service_name] = False
        except requests.exceptions.ConnectionError:
            log(f"{service_name}: CONNECTION ERROR", "WARN")
            results[service_name] = False
        except Exception as e:
            log(f"{service_name}: ERROR - {str(e)}", "WARN")
            results[service_name] = False
    
    # Summary of external service tests
    reachable = sum(1 for v in results.values() if v)
    total = len(results)
    log(f"External services summary: {reachable}/{total} services reachable")
    
    return results

def main():
    log("Starting connectivity tests...")
    log("=" * 60)
    
    results = {}
    
    # Test PostgreSQL (always required)
    results['PostgreSQL'] = test_postgres()
    log("-" * 60)
    
    # Test Azure OpenAI (optional)
    result = test_azure_openai()
    if result is not None:
        results['Azure OpenAI'] = result
        log("-" * 60)
    
    # Test Azure Document Intelligence (optional)
    result = test_azure_document_intelligence()
    if result is not None:
        results['Azure Document Intelligence'] = result
        log("-" * 60)
    
    # Test Ollama (optional)
    result = test_ollama()
    if result is not None:
        results['Ollama'] = result
        log("-" * 60)
    
    # Test OpenAI-compatible endpoint (optional)
    result = test_openai_compatible()
    if result is not None:
        results['OpenAI-compatible'] = result
        log("-" * 60)
    
    # Test Persistent Volume Claim (optional)
    result = test_persistent_volume()
    if result is not None:
        results['Persistent Volume Claim'] = result
        log("-" * 60)
    
    # Test Custom Hostnames (optional)
    custom_results = test_custom_hostnames()
    if custom_results is not None:
        results['Custom Hostnames'] = custom_results
        log("-" * 60)
    
    # Test External Services (optional)
    external_results = test_external_services()
    if external_results is not None:
        results['External Services'] = external_results
        log("-" * 60)
    
    # Summary
    log("=" * 60)
    log("TEST SUMMARY:")
    for service, status in results.items():
        if service in ['Custom Hostnames', 'External Services']:
            # Handle service groups separately
            reachable = sum(1 for v in status.values() if v)
            total = len(status)
            status_text = f"{reachable}/{total} REACHABLE"
            log(f"  {service}: {status_text}")
            for svc_name, svc_status in status.items():
                log(f"    - {svc_name}: {'REACHABLE' if svc_status else 'UNREACHABLE'}")
        else:
            status_text = "PASSED" if status else "FAILED"
            log(f"  {service}: {status_text}")
    
    # Exit with error if any required test failed
    if not results.get('PostgreSQL', False):
        log("Required tests failed!", "ERROR")
        sys.exit(1)
    
    # Keep the pod running for further manual testing
    log("=" * 60)
    log("All required tests completed. Pod will stay running for manual testing.")
    log("To run manual tests, exec into the pod and use:")
    log("  - psql: for PostgreSQL queries")
    log("  - python: for custom Python scripts")
    log("  - curl: for HTTP requests")
    
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()