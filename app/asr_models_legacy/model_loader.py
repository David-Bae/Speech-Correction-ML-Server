from transformers import pipeline, AutoFeatureExtractor, AutoTokenizer, Wav2Vec2ForCTC

#* Debugging
# import logging
# logger = logging.getLogger(__name__)


MODEL_CHECKPOINT = "davidbae/ipa-asr"
VOCAB_FILE_PATH = "/workspace/app/models/vocab.json"
MODEL_NAME = "facebook/wav2vec2-base-960h"

def load_asr_model(model_version): 
    tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT, revision=model_version)
    
    feature_extractor = AutoFeatureExtractor.from_pretrained(MODEL_CHECKPOINT, revision=model_version)
    
    model = Wav2Vec2ForCTC.from_pretrained(
        MODEL_CHECKPOINT,
        revision=model_version,
        ctc_loss_reduction="mean", 
        pad_token_id=tokenizer.pad_token_id,
        vocab_size=len(tokenizer),
    )
    
    pipe = pipeline(
        task="automatic-speech-recognition",
        model=model,
        tokenizer=tokenizer,
        feature_extractor=feature_extractor
    )

    return pipe
