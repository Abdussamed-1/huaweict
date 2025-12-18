"""Check GPU availability and information"""
import sys

def check_gpu():
    """Check if GPU is available and display information."""
    print("=" * 60)
    print("GPU Availability Check")
    print("=" * 60)
    
    try:
        import torch
        print("✅ PyTorch is installed")
        print(f"   Version: {torch.__version__}")
        
        if torch.cuda.is_available():
            print("\n✅ GPU is AVAILABLE!")
            print(f"   GPU Count: {torch.cuda.device_count()}")
            print(f"   Current Device: {torch.cuda.current_device()}")
            print(f"   Device Name: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA Version: {torch.version.cuda}")
            
            # Memory info
            props = torch.cuda.get_device_properties(0)
            total_memory = props.total_memory / 1024**3
            print(f"\n   GPU Memory:")
            print(f"   - Total: {total_memory:.2f} GB")
            print(f"   - Allocated: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
            print(f"   - Reserved: {torch.cuda.memory_reserved(0) / 1024**3:.2f} GB")
            
            print("\n✅ You can use GPU for embeddings!")
            print("   Set EMBEDDING_DEVICE=cuda in .env file")
            return True
        else:
            print("\n⚠️ GPU is NOT available")
            print("   Using CPU for embeddings")
            print("   To use GPU, install CUDA-enabled PyTorch:")
            print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
            return False
            
    except ImportError:
        print("❌ PyTorch is NOT installed")
        print("\nTo enable GPU support:")
        print("1. Install PyTorch with CUDA:")
        print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        print("\n2. Or install CPU-only version:")
        print("   pip install torch")
        return False

if __name__ == "__main__":
    has_gpu = check_gpu()
    print("\n" + "=" * 60)
    if has_gpu:
        print("✅ Ready for GPU-accelerated embeddings!")
    else:
        print("⚠️ Will use CPU for embeddings (slower)")
    print("=" * 60)
    sys.exit(0 if has_gpu else 1)
