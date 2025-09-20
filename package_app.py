#!/usr/bin/env python3
"""
Teams App Packaging Script
Creates a Teams app package (.zip) for upload to Microsoft Teams
"""

import os
import json
import zipfile
import shutil
from pathlib import Path
from typing import List, Dict, Any


def validate_manifest() -> Dict[str, Any]:
    """
    Validate manifest.json file
    
    Returns:
        Parsed manifest data
        
    Raises:
        Exception if manifest is invalid
    """
    manifest_path = Path("manifest.json")
    
    if not manifest_path.exists():
        raise FileNotFoundError("manifest.json not found")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    required_fields = [
        "$schema", "manifestVersion", "version", "id",
        "packageName", "developer", "icons", "name",
        "description", "accentColor", "bots"
    ]
    
    for field in required_fields:
        if field not in manifest:
            raise ValueError(f"Missing required field in manifest: {field}")
    
    print(f"✓ Manifest validated successfully")
    print(f"  App ID: {manifest['id']}")
    print(f"  Name: {manifest['name']['short']}")
    print(f"  Version: {manifest['version']}")
    
    return manifest


def check_icon_files() -> List[str]:
    """
    Check if icon files exist, create placeholders if needed
    
    Returns:
        List of icon file paths
    """
    icons = [
        ("color_icon.png", 192, "🌤️"),
        ("outline_icon.png", 32, "☁️")
    ]
    
    icon_files = []
    
    for filename, size, emoji in icons:
        icon_path = Path(filename)
        
        if not icon_path.exists():
            print(f"⚠️  {filename} not found, creating placeholder...")
            create_placeholder_icon(filename, size, emoji)
        else:
            print(f"✓ Found {filename}")
        
        icon_files.append(filename)
    
    return icon_files


def create_placeholder_icon(filename: str, size: int, emoji: str):
    """
    Create a placeholder icon file
    
    Args:
        filename: Icon filename
        size: Icon size in pixels
        emoji: Emoji to use (for reference)
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        if "color" in filename:
            draw.ellipse([0, 0, size-1, size-1], fill=(66, 133, 244, 255))
            draw.text((size//2, size//2), "W", fill=(255, 255, 255, 255), anchor="mm")
        else:
            draw.ellipse([2, 2, size-3, size-3], outline=(66, 133, 244, 255), width=2)
            draw.text((size//2, size//2), "W", fill=(66, 133, 244, 255), anchor="mm")
        
        image.save(filename)
        print(f"  Created placeholder: {filename}")
        
    except ImportError:
        print(f"  Note: Install 'pillow' package for better icons")
        with open(filename, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82')
        print(f"  Created minimal placeholder: {filename}")


def create_teams_package(manifest: Dict[str, Any], icon_files: List[str]) -> str:
    """
    Create Teams app package (.zip file)
    
    Args:
        manifest: Parsed manifest data
        icon_files: List of icon file paths
        
    Returns:
        Path to created zip file
    """
    package_name = "weather-bot.zip"
    
    if Path(package_name).exists():
        backup_name = f"weather-bot.backup.{int(os.path.getmtime(package_name))}.zip"
        shutil.move(package_name, backup_name)
        print(f"⚠️  Existing package backed up to: {backup_name}")
    
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write("manifest.json")
        print(f"  Added: manifest.json")
        
        for icon_file in icon_files:
            if Path(icon_file).exists():
                zipf.write(icon_file)
                print(f"  Added: {icon_file}")
    
    print(f"✓ Teams app package created: {package_name}")
    
    with zipfile.ZipFile(package_name, 'r') as zipf:
        print(f"  Package contents: {', '.join(zipf.namelist())}")
        print(f"  Package size: {Path(package_name).stat().st_size:,} bytes")
    
    return package_name


def validate_package(package_path: str) -> bool:
    """
    Validate the created package
    
    Args:
        package_path: Path to zip file
        
    Returns:
        True if package is valid
    """
    required_files = ["manifest.json", "color_icon.png", "outline_icon.png"]
    
    with zipfile.ZipFile(package_path, 'r') as zipf:
        files_in_zip = zipf.namelist()
        
        for required_file in required_files:
            if required_file not in files_in_zip:
                print(f"✗ Missing required file in package: {required_file}")
                return False
    
    print("✓ Package validation successful")
    return True


def update_manifest_url(cloud_run_url: str = None):
    """
    Update manifest with actual Cloud Run URL
    
    Args:
        cloud_run_url: Deployed Cloud Run URL
    """
    if cloud_run_url:
        manifest_path = Path("manifest.json")
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        manifest["validDomains"] = [cloud_run_url.replace("https://", "")]
        
        webhook_url = f"{cloud_run_url}/api/teams/webhook"
        if "bots" in manifest and manifest["bots"]:
            if "messagingEndpoint" not in manifest["bots"][0]:
                manifest["bots"][0]["messagingEndpoint"] = {}
            manifest["bots"][0]["messagingEndpoint"]["url"] = webhook_url
        
        if "webApplicationInfo" in manifest:
            manifest["webApplicationInfo"]["resource"] = f"api://{cloud_run_url.replace('https://', '')}/{manifest['id']}"
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=4)
        
        print(f"✓ Updated manifest with Cloud Run URL: {cloud_run_url}")
        return True
    
    return False


def main():
    """Main packaging function"""
    print("\n" + "="*50)
    print("Teams App Packaging Tool")
    print("="*50 + "\n")
    
    try:
        print("Step 1: Validating manifest.json...")
        manifest = validate_manifest()
        
        print("\nStep 2: Checking icon files...")
        icon_files = check_icon_files()
        
        print("\nStep 3: Creating Teams app package...")
        package_path = create_teams_package(manifest, icon_files)
        
        print("\nStep 4: Validating package...")
        if validate_package(package_path):
            print("\n" + "="*50)
            print("✅ SUCCESS: Teams app package ready!")
            print("="*50)
            print(f"\nPackage location: {os.path.abspath(package_path)}")
            print("\nNext steps:")
            print("1. Deploy to Google Cloud Run: ./deploy.sh")
            print("2. Update manifest with Cloud Run URL")
            print("3. Repackage with: python package_app.py")
            print("4. Upload to Teams: Apps → Upload a custom app")
            
            cloud_run_url = os.getenv("CLOUD_RUN_URL")
            if cloud_run_url:
                print(f"\n⚠️  Found CLOUD_RUN_URL: {cloud_run_url}")
                response = input("Update manifest with this URL? (y/n): ")
                if response.lower() == 'y':
                    if update_manifest_url(cloud_run_url):
                        print("Repackaging with updated URL...")
                        create_teams_package(manifest, icon_files)
        else:
            print("\n✗ Package validation failed")
            return 1
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())