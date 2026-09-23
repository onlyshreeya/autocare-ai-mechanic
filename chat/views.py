
import os
import json
import mimetypes
from datetime import datetime, date

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from google import genai
from google.genai import types
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from .models import ChatMessage, MediaUpload, Diagnosis, Booking


# System Prompt: Conversational Senior Automobile Technician Persona
SYSTEM_PROMPT = """
You are a friendly, experienced Senior Master Automobile Technician having a natural, 1-on-1 real-time conversation with a car owner.

Strict Operating Rules:
1. CONVERSATIONAL TONALITY: Talk like a friendly, experienced mechanic having a natural conversation with a customer in the shop. Keep your replies short, natural, and easy to understand (usually 1–3 sentences).
2. NO LONG STRUCTURED REPORTS OR BULLET LISTS: Avoid long structured reports, excessive bullet points, markdown headings, numbered lists, or dumping full troubleshooting manuals unless the user explicitly requests a detailed breakdown.
3. ONE QUESTION AT A TIME: Ask only ONE relevant follow-up question at a time to narrow down the problem. Wait for the customer's answer before asking the next question.
4. BE CONVERSATIONAL & EMPOWERING:
   - If the user says "My car won't start", respond conversationally, such as: "Okay, let's figure it out. When you turn the key, do you hear the engine cranking, or is there just a clicking sound?"
   - If the user answers "Just clicking", continue naturally using that context.
5. CONVERSATION HISTORY MEMORY: Use recent chat history to understand follow-up messages. Never ask the user to repeat information they have already provided (like vehicle year/make/model, symptoms, or noises).
6. SIMPLE EXPLANATIONS: Explain possible causes in simple language, like a mechanic talking to a customer. Don't immediately list every possible cause or give a full troubleshooting guide at once. Provide a detailed explanation only when the user asks for one or when it is genuinely necessary for safety.
7. AUTOMOTIVE DOMAIN RESTRICTION: Only answer questions related to motor vehicles, cars, trucks, motorcycles, engine components, brakes, tires, vehicle electronics, and automotive maintenance. If the user asks an off-topic question, politely decline in 1-2 short friendly sentences and remind them that you specialize strictly in automotive care.
8. SAFETY GUIDANCE: Always emphasize safety. If an issue sounds dangerous (e.g. brake failure, severe overheating, low oil pressure), advise pulling over safely or getting professional mechanic assistance.
9. GREETINGS & CASUAL MESSAGES: Keep greetings and casual chat warm, friendly, and brief (1-2 sentences).
"""


def get_rule_based_reply(message):
    """
    Handle common greetings, casual chit-chat, and off-topic filtering locally to minimize Gemini API calls.
    Troubleshooting queries pass through to Gemini AI to ensure full conversational flow and multi-turn context.
    """
    msg = message.lower().strip()

    # 1. Greetings & Chit-Chat
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings", "howdy"]
    if msg in greetings or any(msg.startswith(g + " ") for g in greetings if len(msg) < 15):
        return (
            "Hello! I'm your Senior AI Car Mechanic Assistant. "
            "What's going on with your vehicle today?"
        )

    if any(phrase in msg for phrase in ["who are you", "what can you do", "what do you do"]):
        return (
            "I am a virtual Senior Automobile Technician. I can help troubleshoot vehicle problems, "
            "inspect photos/videos of car issues, and help you book a mechanic."
        )

    if any(phrase in msg for phrase in ["thank you", "thanks", "thank u", "thx"]):
        return "You're very welcome! Drive safely, and let me know if you need any more assistance with your car."

    if any(phrase in msg for phrase in ["bye", "goodbye", "see ya", "cya"]):
        return "Goodbye! Drive safely and take good care of your car!"

    # 2. Domain Filter Guard (Politely reject non-car queries without calling AI)
    off_topic_indicators = [
        "recipe", "cook", "kitchen", "python", "javascript", "code", "programming",
        "president", "capital of", "weather today", "tell me a joke", "write an essay",
        "math equation", "crypto", "bitcoin", "movie recommendation", "song lyrics"
    ]
    if any(indicator in msg for indicator in off_topic_indicators):
        return (
            "I am an AI Car Mechanic Assistant specialized strictly in automotive diagnostics "
            "and vehicle maintenance. I can't assist with non-car topics, but feel free to ask me anything about your vehicle!"
        )

    return None


def get_conversational_fallback(user_message, history=None):
    """
    Dynamic conversational fallback when Gemini API experiences high demand or network delays.
    Provides natural 1-3 sentence mechanic responses matching the system prompt.
    """
    msg = user_message.lower().strip()

    recent_text = ""
    if history and isinstance(history, list) and len(history) > 0:
        last_turn = history[-1]
        recent_text = (last_turn.get("text") or last_turn.get("user_message") or "").lower()

    if "clicking" in msg or "just clicking" in msg or ("clicking" in recent_text and "yes" in msg):
        return "A clicking sound usually points to a weak battery or a loose terminal connection. Do your headlights turn on, or are they dim as well?"

    if "cranking" in msg or "slow crank" in msg:
        return "Slow cranking usually means low battery voltage or a failing starter motor. Have you tried jump-starting the vehicle?"

    if "won't start" in msg or "will not start" in msg or "car dead" in msg:
        return "Okay, let's figure it out. When you turn the key, do you hear the engine cranking, or is there just a clicking sound?"

    if "beep" in msg or "chime" in msg or "buzz" in msg:
        return "Beeping sounds often point to unbuckled seatbelts, a door or trunk slightly open, or low tire pressure. Does the beeping happen while driving or as soon as you start the car?"

    if "overheating" in msg or "engine hot" in msg or "steam" in msg:
        return "Pull over safely immediately and turn off the engine. Is there steam coming from under the hood, or did a temperature warning light turn on?"

    if "brake" in msg or "squeak" in msg or "grinding" in msg:
        return "Brake noises are usually a sign of worn pads or rotors. Does the squealing or grinding happen every time you step on the pedal?"

    if "check engine" in msg or "warning light" in msg:
        return "A check engine light means the computer stored a diagnostic code. Is the light steady, or is it flashing?"

    return "Got it. Could you tell me a bit more about when that happens or if any warning lights popped up on your dashboard?"


import concurrent.futures


def get_gemini_reply(user_message, history=None, media_obj=None):
    """Call Gemini API with a 25-second timeout. Falls back gracefully if API is unreachable."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("Gemini API key is missing. Please set GEMINI_API_KEY in .env file.")

    system_ctx = SYSTEM_PROMPT.strip()

    history_ctx = ""
    if history and isinstance(history, list):
        turns = []
        for item in history[-10:]:
            role = "User" if item.get("role") == "user" or "user_message" in item else "Technician"
            text = item.get("text") or item.get("user_message") or item.get("bot_reply") or ""
            if text:
                turns.append(f"{role}: {text}")
        if turns:
            history_ctx = "\nRecent Conversation History:\n" + "\n".join(turns) + "\n"

    prompt_text = f"{system_ctx}\n{history_ctx}\nCurrent User Input:\n{user_message}"
    contents = [prompt_text]

    if media_obj and media_obj.file:
        try:
            file_path = media_obj.file.path
            if os.path.exists(file_path):
                mime_type, _ = mimetypes.guess_type(file_path)
                if not mime_type:
                    mime_type = f"{media_obj.media_type}/*"
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                media_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
                contents.append(media_part)
        except Exception as media_err:
            print("Failed to attach media to Gemini request:", str(media_err))

    def _call_gemini():
        client = genai.Client(api_key=api_key)
        for model_name in ["gemini-3.6-flash", "gemini-3.7-flash", "gemini-flash-latest"]:
            try:
                resp = client.models.generate_content(model=model_name, contents=contents)
                if resp and resp.text:
                    return resp.text
            except Exception as e:
                print(f"Model {model_name} error: {e}")
        return None

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(_call_gemini)
            reply = future.result(timeout=25.0)
            if reply:
                return reply
    except Exception as timeout_err:
        print("Gemini API timeout/error:", str(timeout_err))

    return get_conversational_fallback(user_message, history=history)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def chat_home(request):
    """
    POST /api/chat/ - Send message to chat assistant
    GET  /api/chat/ - Retrieve chat history
    """
    # GET: Return chat history
    if request.method == "GET":
        messages = ChatMessage.objects.order_by("created_at")
        history = [
            {
                "id": message.id,
                "user_message": message.user_message,
                "bot_reply": message.bot_reply,
                "created_at": message.created_at.isoformat()
            }
            for message in messages
        ]
        return JsonResponse({"history": history})

    # POST: Handle incoming user message
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON format."}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "Request body must be a JSON object."}, status=400)

    user_message = data.get("message", "")
    history_context = data.get("history", [])
    media_id = data.get("media_id")

    if not isinstance(user_message, str):
        return JsonResponse({"error": "Message must be text."}, status=400)

    user_message = user_message.strip()

    # Load media object if media_id is provided
    media_obj = None
    if media_id:
        try:
            media_obj = MediaUpload.objects.get(id=media_id)
        except MediaUpload.DoesNotExist:
            pass

    if not user_message and not media_obj:
        return JsonResponse({"error": "Message or uploaded media is required."}, status=400)

    if not user_message and media_obj:
        user_message = f"Please inspect this uploaded vehicle {media_obj.media_type} ({media_obj.original_filename}) and analyze any issues."

    # Step 1: Check local rules & domain guards first (Minimizing AI calls)
    bot_reply = get_rule_based_reply(user_message)

    if bot_reply and not media_obj:
        provider = "Rule-based Engine"
    else:
        # Step 2: Call Gemini for complex queries or multimodal media analysis
        try:
            bot_reply = get_gemini_reply(user_message, history=history_context, media_obj=media_obj)
            provider = "Gemini AI"
        except Exception as error:
            print("Gemini call failed:", str(error))
            bot_reply = get_conversational_fallback(user_message, history=history_context)
            provider = "Conversational Engine"

    # Step 3: Save conversation in SQLite DB
    chat_message = ChatMessage.objects.create(
        user_message=user_message,
        bot_reply=bot_reply
    )

    return JsonResponse({
        "id": chat_message.id,
        "user_message": chat_message.user_message,
        "bot_reply": chat_message.bot_reply,
        "provider": provider,
        "created_at": chat_message.created_at.isoformat()
    }, status=201)


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_media(request):
    """
    POST /api/upload/ and POST /api/chat/upload/
    Uploads image, video, or audio file up to 20MB.
    """
    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

    # Maximum file size: 20 MB
    if uploaded_file.size > 20 * 1024 * 1024:
        return Response({"error": "File size cannot exceed 20 MB"}, status=status.HTTP_400_BAD_REQUEST)

    # Allowed file extensions
    allowed_types = {
        "image": [".jpg", ".jpeg", ".png", ".webp"],
        "video": [".mp4", ".mov", ".webm"],
        "audio": [".mp3", ".wav", ".m4a", ".ogg"],
    }

    extension = os.path.splitext(uploaded_file.name)[1].lower()
    media_type = None

    for file_type, extensions in allowed_types.items():
        if extension in extensions:
            media_type = file_type
            break

    if not media_type:
        return Response({"error": "Unsupported file type. Please upload images, videos, or audio files."}, status=status.HTTP_400_BAD_REQUEST)

    media = MediaUpload.objects.create(
        file=uploaded_file,
        original_filename=uploaded_file.name,
        media_type=media_type,
        file_size=uploaded_file.size
    )

    return Response({
        "message": "File uploaded successfully",
        "id": media.id,
        "filename": media.original_filename,
        "media_type": media.media_type,
        "file_size": media.file_size,
        "file_url": request.build_absolute_uri(media.file.url)
    }, status=status.HTTP_201_CREATED)


def get_diagnosis(symptoms):
    """Rule-based vehicle diagnosis lookup."""
    sym = symptoms.lower()

    if "overheat" in sym or "hot engine" in sym or "coolant" in sym:
        return {
            "result": "Likely Cooling System Failure. Possible issues: low coolant level, stuck thermostat, failing water pump, or radiator fan malfunction.",
            "severity": "High"
        }
    elif "won't start" in sym or "not starting" in sym or "clicking" in sym:
        return {
            "result": "Likely Electrical/Starting System Issue. Possible issues: discharged battery, corroded terminals, faulty starter motor, or alternator failure.",
            "severity": "Medium"
        }
    elif "brake" in sym and ("noise" in sym or "sound" in sym or "squeak" in sym or "grind" in sym):
        return {
            "result": "Likely Brake Component Wear. Possible issues: worn brake pads, scored rotors, or lack of brake lubrication.",
            "severity": "High"
        }
    elif "flat tyre" in sym or "flat tire" in sym or "puncture" in sym:
        return {
            "result": "Tyre Damage/Puncture. Avoid driving on rim to prevent expensive wheel damage.",
            "severity": "Medium"
        }
    elif "check engine" in sym or "warning light" in sym:
        return {
            "result": "Powertrain / Diagnostic Trouble Code (DTC) active. Requires OBD-II scanner reading.",
            "severity": "Medium"
        }
    else:
        return None


@api_view(["GET", "POST"])
def diagnosis_api(request):
    """
    POST /api/diagnosis/ - Generate vehicle diagnosis
    GET  /api/diagnosis/ - Get diagnosis history
    """
    if request.method == "GET":
        records = Diagnosis.objects.all().order_by("-created_at")
        history = [
            {
                "id": record.id,
                "vehicle_model": record.vehicle_model,
                "symptoms": record.symptoms,
                "diagnosis": record.diagnosis_result,
                "diagnosis_result": record.diagnosis_result,
                "severity": record.severity,
                "created_at": record.created_at.isoformat()
            }
            for record in records
        ]
        return Response(history, status=status.HTTP_200_OK)

    symptoms = request.data.get("symptoms", "").strip()
    vehicle_model = request.data.get("vehicle_model", "").strip()

    if not symptoms:
        return Response({"error": "Please provide car symptoms"}, status=status.HTTP_400_BAD_REQUEST)

    # Try local diagnosis rules first
    diagnosis = get_diagnosis(symptoms)

    # Fallback to Gemini diagnosis if symptoms are detailed/unmatched
    if not diagnosis:
        try:
            ai_diag = get_gemini_reply(f"Provide a concise automotive diagnosis and severity for these symptoms on a {vehicle_model or 'vehicle'}: {symptoms}")
            diagnosis = {
                "result": ai_diag,
                "severity": "Medium"
            }
        except Exception:
            diagnosis = {
                "result": "Unable to pinpoint exact issue from symptoms provided. Please consult a qualified mechanic for hands-on inspection.",
                "severity": "Unknown"
            }

    record = Diagnosis.objects.create(
        vehicle_model=vehicle_model or "Not specified",
        symptoms=symptoms,
        diagnosis_result=diagnosis["result"],
        severity=diagnosis["severity"]
    )

    return Response({
        "message": "Diagnosis generated successfully",
        "diagnosis_id": record.id,
        "vehicle_model": record.vehicle_model,
        "symptoms": record.symptoms,
        "diagnosis": record.diagnosis_result,
        "diagnosis_result": record.diagnosis_result,
        "severity": record.severity,
        "created_at": record.created_at.isoformat()
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def booking_api(request):
    """
    POST /api/booking/ - Create a new mechanic appointment booking
    """
    customer_name = request.data.get("customer_name", "").strip()
    phone = request.data.get("phone", "").strip()
    vehicle_model = request.data.get("vehicle_model", "").strip()
    issue_description = request.data.get("issue_description", "").strip()
    appointment_date_raw = request.data.get("appointment_date", "")
    appointment_time_raw = request.data.get("appointment_time", "")

    if not all([customer_name, phone, vehicle_model, issue_description, appointment_date_raw, appointment_time_raw]):
        return Response({"error": "Please provide all required booking fields."}, status=status.HTTP_400_BAD_REQUEST)

    # Clean phone string (allow digits, +, -)
    clean_phone = "".join([c for c in phone if c.isdigit()])
    if not 10 <= len(clean_phone) <= 15:
        return Response({"error": "Please provide a valid phone number (10-15 digits)."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        app_date = datetime.strptime(appointment_date_raw, "%Y-%m-%d").date()
        app_time = datetime.strptime(appointment_time_raw, "%H:%M").time()
    except ValueError:
        return Response({"error": "Use date format YYYY-MM-DD and time format HH:MM"}, status=status.HTTP_400_BAD_REQUEST)

    if app_date < date.today():
        return Response({"error": "Appointment date cannot be in the past."}, status=status.HTTP_400_BAD_REQUEST)

    existing_booking = Booking.objects.filter(
        appointment_date=app_date,
        appointment_time=app_time,
        status__in=["pending", "confirmed"]
    ).exists()

    if existing_booking:
        return Response({
            "error": "This appointment slot is already booked. Please choose another time slot."
        }, status=status.HTTP_409_CONFLICT)

    booking = Booking.objects.create(
        customer_name=customer_name,
        phone=phone,
        vehicle_model=vehicle_model,
        issue_description=issue_description,
        appointment_date=app_date,
        appointment_time=app_time
    )

    return Response({
        "message": "Booking request created successfully",
        "booking_id": booking.id,
        "customer_name": booking.customer_name,
        "phone": booking.phone,
        "vehicle_model": booking.vehicle_model,
        "issue_description": booking.issue_description,
        "appointment_date": str(booking.appointment_date),
        "appointment_time": booking.appointment_time.strftime("%H:%M"),
        "status": booking.status,
        "created_at": booking.created_at.isoformat()
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def get_booking_by_id(request, booking_id):
    """
    GET /api/booking/{id}/ - Retrieve single booking by ID (Minimum API Requirement)
    """
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({"error": f"Booking with ID {booking_id} was not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "booking_id": booking.id,
        "customer_name": booking.customer_name,
        "phone": booking.phone,
        "vehicle_model": booking.vehicle_model,
        "issue_description": booking.issue_description,
        "appointment_date": str(booking.appointment_date),
        "appointment_time": booking.appointment_time.strftime("%H:%M"),
        "status": booking.status,
        "created_at": booking.created_at.isoformat()
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_bookings(request):
    """
    GET /api/bookings/ - List all bookings
    """
    bookings = Booking.objects.all().order_by("-created_at")
    data = [
        {
            "booking_id": booking.id,
            "customer_name": booking.customer_name,
            "phone": booking.phone,
            "vehicle_model": booking.vehicle_model,
            "issue_description": booking.issue_description,
            "appointment_date": str(booking.appointment_date),
            "appointment_time": booking.appointment_time.strftime("%H:%M"),
            "status": booking.status,
            "created_at": booking.created_at.isoformat()
        }
        for booking in bookings
    ]
    return Response({
        "total_bookings": len(data),
        "bookings": data
    }, status=status.HTTP_200_OK)


@api_view(["PATCH"])
def update_booking_status(request, booking_id):
    """
    PATCH /api/bookings/{id}/status/ - Update booking status (confirmed or cancelled)
    """
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

    if booking.status == "cancelled":
        return Response({"error": "Cancelled bookings cannot be modified."}, status=status.HTTP_400_BAD_REQUEST)

    new_status = request.data.get("status")
    if new_status not in ["confirmed", "cancelled"]:
        return Response({"error": "Status must be 'confirmed' or 'cancelled'."}, status=status.HTTP_400_BAD_REQUEST)

    booking.status = new_status
    booking.save()

    return Response({
        "message": "Booking status updated successfully",
        "booking_id": booking.id,
        "status": booking.status
    }, status=status.HTTP_200_OK)