import { Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { FiSettings, FiUser, FiLogOut, FiMoon, FiSun } from 'react-icons/fi';

export default function SettingsDropdown() {
  return (
    <Menu as="div" className="relative inline-block text-left">
      <div>
        <Menu.Button className="inline-flex w-full justify-center items-center px-4 py-2 text-sm font-medium text-gray-200 hover:bg-gray-700 rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-opacity-75">
          <FiSettings className="w-5 h-5" />
        </Menu.Button>
      </div>
      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right divide-y divide-gray-700 rounded-md bg-[#1C1E21] shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
          <div className="px-1 py-1">
            <Menu.Item>
              {({ active }) => (
                <button
                  className={`${
                    active ? 'bg-gray-700 text-white' : 'text-gray-200'
                  } group flex w-full items-center rounded-md px-2 py-2 text-sm`}
                >
                  <FiUser className="mr-2 h-5 w-5" />
                  Profile
                </button>
              )}
            </Menu.Item>
            <Menu.Item>
              {({ active }) => (
                <button
                  className={`${
                    active ? 'bg-gray-700 text-white' : 'text-gray-200'
                  } group flex w-full items-center rounded-md px-2 py-2 text-sm`}
                >
                  <FiMoon className="mr-2 h-5 w-5" />
                  Dark Mode
                </button>
              )}
            </Menu.Item>
          </div>
          <div className="px-1 py-1">
            <Menu.Item>
              {({ active }) => (
                <button
                  className={`${
                    active ? 'bg-gray-700 text-white' : 'text-gray-200'
                  } group flex w-full items-center rounded-md px-2 py-2 text-sm`}
                >
                  <FiLogOut className="mr-2 h-5 w-5" />
                  Logout
                </button>
              )}
            </Menu.Item>
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  );
} 