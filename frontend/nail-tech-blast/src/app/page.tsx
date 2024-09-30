import { upload_csv_button } from '@/components/upload-csv-button';
import { GroupMessageFormComponent } from '@/components/group-message-form';

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-md p-4 bg-white rounded shadow-lg">
        <h1 className="text-2xl font-bold text-center mb-4">Send a Text Blast</h1>
        
        {/* CSV Upload Button component */}
        {upload_csv_button()}

        {/* Group Message Form component */}
        <GroupMessageFormComponent />
      </div>
    </div>
  );
}
