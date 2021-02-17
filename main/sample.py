import pyaudio
import wave
import json
import textwrap
import argparse


from vosk import Model, KaldiRecognizer

model = Model('../resource/model')
recognizer = KaldiRecognizer(model, 16000)


def play_and_decode(wav_file, output_file):
    chunk = 1024
    # create an interface to PortAudio
    p = pyaudio.PyAudio()

    # open wav file
    wf = wave.open(wav_file, 'rb')

    # open a .Stream object to write the WAV file to
    # 'output = True' indicates that the sound will be played rather than recorded
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # open trans writer
    writer = open(output_file, 'w', encoding='UTF-8')

    counter = 1
    flag = 0
    text = ''

    while True:
        # read data in chunks
        data = wf.readframes(chunk)
        if len(data) == 0:
            break

        # play the sound by writing the audio data to the stream
        stream.write(data)

        # decode wav
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get('text')

            writer.write('%s\n' % text)
            writer.flush()

            counter += 1
            flag = 0
        else:
            if flag == 0:
                print('\n-----> #%s\n' % counter)
                flag = 1

            result = json.loads(recognizer.PartialResult())
            trans = result.get('partial')
            if trans == '':
                continue

            print(textwrap.fill(trans, 200) + '\n')

    # close the stream
    p.terminate()
    stream.close()
    writer.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--wav-file', type=str)
    args = parser.parse_args()

    play_and_decode(args.wav_file)
